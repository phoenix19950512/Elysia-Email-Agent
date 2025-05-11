# type: ignore

import os
import cv2
import pytesseract
from pdfminer.high_level import extract_text
from app.models.schema import FileProcessingResult

class FileService:
    def __init__(self):
        self.supported_types = ["pdf", "png", "jpg", "jpeg", "txt"]
        self.upload_dir = os.path.join(os.getcwd(), "uploads")
        
        # Create uploads directory if it doesn't exist
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
    
    def process_file(self, file_path):
        """Process a file and extract text based on file type"""
        file_type = file_path.split(".")[-1].lower()
        
        if file_type not in self.supported_types:
            return FileProcessingResult(
                extracted_text="Unsupported file type. Please upload a PDF, image, or text file.",
                summary="Error: Unsupported file type",
                keywords=[]
            )
        
        extracted_text = ""
        
        try:
            if file_type == "pdf":
                extracted_text = self._extract_text_from_pdf(file_path)
            elif file_type in ["png", "jpg", "jpeg"]:
                extracted_text = self._extract_text_from_image(file_path)
            elif file_type == "txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    extracted_text = f.read()
            
            # Generate a simple summary (first 200 characters)
            summary = extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
            
            # Extract keywords
            words = extracted_text.split()
            keywords = list(set([word.lower() for word in words if len(word) > 5]))[:10]
            
            return FileProcessingResult(
                extracted_text=extracted_text,
                summary=summary,
                keywords=keywords
            )
            
        except Exception as e:
            return FileProcessingResult(
                extracted_text=f"Error processing file: {str(e)}",
                summary="Error occurred during processing",
                keywords=[]
            )
    
    def _extract_text_from_pdf(self, file_path):
        """Extract text from a PDF file"""
        return extract_text(file_path)
    
    def _extract_text_from_image(self, file_path):
        """Extract text from an image file using OCR"""
        image = cv2.imread(file_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply image preprocessing for better OCR results
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        # Extract text using pytesseract
        text = pytesseract.image_to_string(gray)
        return text
    
    def save_uploaded_file(self, file):
        """Save an uploaded file and return the file path"""
        filename = file.filename
        file_path = os.path.join(self.upload_dir, filename)
        
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        
        return file_path
