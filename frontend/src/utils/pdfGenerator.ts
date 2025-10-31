import jsPDF from 'jspdf';
import type { Message } from '../types';

export const generateChatPDF = (messages: Message[]): void => {
  if (messages.length === 0) return;

  // Create PDF
  const pdf = new jsPDF('p', 'mm', 'a4');
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 20;
  const contentWidth = pageWidth - 2 * margin;
  const maxBubbleWidth = contentWidth * 0.7; // Limit bubble width to 70% of content width
  
  let yPosition = margin + 20;

  // Add header
  pdf.setFillColor(255, 140, 0);
  pdf.rect(0, 0, pageWidth, 30, 'F');
  
  // Add title
  pdf.setTextColor(255, 255, 255);
  pdf.setFontSize(24);
  pdf.setFont('helvetica', 'bold');
  pdf.text('Tiggy Chat', margin, 20);
  
  // Add date
  pdf.setFontSize(12);
  pdf.setFont('helvetica', 'normal');
  const currentDate = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  pdf.text(currentDate, pageWidth - margin - pdf.getTextWidth(currentDate), 20);

  // Reset text color for messages
  pdf.setTextColor(0, 0, 0);
  yPosition = 50;

  // Add messages
  messages.forEach((message) => {
    const sender = message.isUser ? 'You' : 'Tiggy';
    const time = message.timestamp.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
    
    // Check if we need a new page
    if (yPosition > pageHeight - 40) {
      pdf.addPage();
      yPosition = margin;
    }

    // Add timestamp
    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'italic');
    pdf.setTextColor(100, 100, 100);
    
    if (message.isUser) {
      // Right-align timestamp for user messages
      const timestampText = `[${time}] ${sender}`;
      const timestampX = pageWidth - margin - pdf.getTextWidth(timestampText);
      pdf.text(timestampText, timestampX, yPosition);
    } else {
      // Left-align timestamp for AI messages
      pdf.text(`[${time}] ${sender}`, margin, yPosition);
    }
    yPosition += 5;

    // Add message bubble
    pdf.setFontSize(12);
    pdf.setFont('helvetica', 'normal');
    
    if (message.isUser) {
      // User message - right aligned with orange background
      pdf.setFillColor(255, 140, 0);
      pdf.setTextColor(255, 255, 255);
      
      // Calculate text width and bubble dimensions with proper wrapping
      const textLines = pdf.splitTextToSize(message.message, maxBubbleWidth - 20);
      const lineHeight = 6;
      const bubbleHeight = textLines.length * lineHeight + 16;
      const bubbleWidth = Math.min(
        Math.max(...textLines.map((line: string) => pdf.getTextWidth(line))) + 20,
        maxBubbleWidth
      );
      const bubbleX = pageWidth - margin - bubbleWidth;
      
      // Draw bubble
      pdf.roundedRect(bubbleX, yPosition, bubbleWidth, bubbleHeight, 3, 3, 'F');
      
      // Add text with proper positioning
      textLines.forEach((line: string, index: number) => {
        pdf.text(line, bubbleX + 10, yPosition + 12 + (index * lineHeight));
      });
      
      yPosition += bubbleHeight + 10;
    } else {
      // AI message - left aligned with white background
      pdf.setFillColor(240, 240, 240);
      pdf.setTextColor(0, 0, 0);
      
      // Calculate text width and bubble dimensions with proper wrapping
      const textLines = pdf.splitTextToSize(message.message, maxBubbleWidth - 20);
      const lineHeight = 6;
      const bubbleHeight = textLines.length * lineHeight + 16;
      const bubbleWidth = Math.min(
        Math.max(...textLines.map((line: string) => pdf.getTextWidth(line))) + 20,
        maxBubbleWidth
      );
      
      // Draw bubble
      pdf.roundedRect(margin, yPosition, bubbleWidth, bubbleHeight, 3, 3, 'F');
      
      // Add text with proper positioning
      textLines.forEach((line: string, index: number) => {
        pdf.text(line, margin + 10, yPosition + 12 + (index * lineHeight));
      });
      
      yPosition += bubbleHeight + 10;
    }
  });

  // Save the PDF
  const fileName = `tiggy-chat-${new Date().toISOString().split('T')[0]}.pdf`;
  pdf.save(fileName);
}; 