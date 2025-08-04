const API_BASE_URL = 'http://localhost:8000';

export const api = {
  generateTutorial: async (data) => {
    try {
      console.log('Sending request to:', `${API_BASE_URL}/generate`);
      console.log('Request data:', data);
      
      const response = await fetch(`${API_BASE_URL}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      const result = await response.json();
      console.log('Response data:', result);
      return result;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  getTaskStatus: async (taskId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/status/${taskId}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      console.error('Status API Error:', error);
      throw error;
    }
  },

  getOutputFiles: async (taskId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/output/${taskId}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      console.error('Output API Error:', error);
      throw error;
    }
  },

  generatePDF: async (pdfData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/generate-pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(pdfData),
      });

      if (!response.ok) {
        throw new Error(`PDF generation failed: ${response.status}`);
      }

      // For HTML response that can be printed as PDF
      const htmlContent = await response.text();
      
      // Open in new window for printing
      const printWindow = window.open('', '_blank');
      printWindow.document.write(htmlContent);
      printWindow.document.close();
      
      return true;
    } catch (error) {
      console.error('PDF generation error:', error);
      throw error;
    }
  },

  getTasks: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      console.error('Tasks API Error:', error);
      throw error;
    }
  }
};

export default api;
