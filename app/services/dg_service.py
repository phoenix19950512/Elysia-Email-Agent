import asyncio
from deepgram import DeepgramClient, LiveOptions
from config import DEEPGRAM_API_KEY

dg_client = DeepgramClient(DEEPGRAM_API_KEY)
options = LiveOptions(
    model="nova-3",
    language='en',
    smart_format=True,
    interim_results=True,
    utterance_end_ms='1000',
    vad_events=True,
    endpointing=500,
)

async def relay_transcripts(sio, sid, dg_socket):
    async for msg in dg_socket:
        await sio.emit("transcript", msg, to=sid)

async def process_audio_chunk(sio, sid, data: bytes):
    if not hasattr(sio, f"dg_socket_{sid}"):
        dg_socket = dg_client.listen.asyncwebsocket.v("1")
        setattr(sio, f"dg_socket_{sid}", dg_socket)
        await dg_socket.start(options)

        asyncio.create_task(relay_transcripts(sid, dg_socket))

    dg_socket = getattr(sio, f"dg_socket_{sid}")
    await dg_socket.send(data)

async def finish_deepgram(sio, sid):
    dg_socket = getattr(sio, f"dg_socket_{sid}", None)
    if dg_socket:
        await dg_socket.finish()
        delattr(sio, f"dg_socket_{sid}")
