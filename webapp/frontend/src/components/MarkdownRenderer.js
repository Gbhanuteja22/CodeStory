import React from 'react';
import CodeBlock from './CodeBlock';

const MarkdownRenderer = ({ content }) => {
  if (!content) return null;

  const processMarkdown = (text) => {
    // Clean up the text first
    const cleanedText = text
      .replace(/\n{3,}/g, '\n\n') // Remove excessive line breaks
      .replace(/_{3,}/g, '') // Remove excessive underscores
      .trim();
    
    const lines = cleanedText.split('\n');
    const elements = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i].trim();
      
      // Skip empty lines
      if (!line) {
        i++;
        continue;
      }

      // Code blocks (```) - handle multi-line code blocks
      if (line.startsWith('```')) {
        const language = line.slice(3).trim();
        const codeLines = [];
        i++;
        
        while (i < lines.length && !lines[i].trim().startsWith('```')) {
          codeLines.push(lines[i]);
          i++;
        }
        
        // Special handling for flowcharts and diagrams
        const isFlowchart = language.toLowerCase().includes('mermaid') || 
                          language.toLowerCase().includes('flowchart') ||
                          codeLines.some(line => line.includes('flowchart') || line.includes('graph'));
        
        if (isFlowchart) {
          // Format flowchart with better styling
          elements.push(
            <div key={elements.length} className="my-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <div className="text-sm text-blue-700 dark:text-blue-300 mb-2 font-medium">
                📊 Flowchart Diagram
              </div>
              <CodeBlock language={language} className={`language-${language}`}>
                {codeLines.join('\n')}
              </CodeBlock>
            </div>
          );
        } else {
          elements.push(
            <CodeBlock key={elements.length} language={language} className={`language-${language}`}>
              {codeLines.join('\n')}
            </CodeBlock>
          );
        }
        
        i++; // Skip closing ```
        continue;
      }

      // Headers - properly format markdown headers
      if (line.startsWith('#')) {
        const level = line.match(/^#+/)[0].length;
        const headerText = line.replace(/^#+\s*/, '').replace(/_/g, ' '); // Clean underscores from titles
        const HeaderTag = `h${Math.min(level, 6)}`;
        const headerClasses = {
          1: 'text-3xl font-bold mb-6 mt-8 text-gray-900 dark:text-gray-100 border-b-2 border-gray-200 dark:border-gray-600 pb-2',
          2: 'text-2xl font-bold mb-4 mt-6 text-gray-800 dark:text-gray-200',
          3: 'text-xl font-semibold mb-3 mt-5 text-gray-800 dark:text-gray-200',
          4: 'text-lg font-semibold mb-2 mt-4 text-gray-700 dark:text-gray-300',
          5: 'text-base font-semibold mb-2 mt-3 text-gray-700 dark:text-gray-300',
          6: 'text-sm font-semibold mb-1 mt-2 text-gray-600 dark:text-gray-400'
        };
        
        elements.push(
          React.createElement(HeaderTag, {
            key: elements.length,
            className: headerClasses[level] || headerClasses[6]
          }, headerText)
        );
        i++;
        continue;
      }

      // Lists
      if (line.match(/^\s*[-*+]\s/) || line.match(/^\s*\d+\.\s/)) {
        const listItems = [];
        const isOrdered = line.match(/^\s*\d+\.\s/);
        
        while (i < lines.length) {
          const currentLine = lines[i].trim();
          if (!currentLine) {
            i++;
            continue;
          }
          
          if (currentLine.match(/^\s*[-*+]\s/) || currentLine.match(/^\s*\d+\.\s/)) {
            const itemText = currentLine.replace(/^\s*(?:[-*+]|\d+\.)\s/, '');
            
            // Clean up the item text and handle different formats
            const cleanedItemText = itemText.replace(/__+/g, '_').replace(/_/g, ' ').trim();
            
            // Check if it's a chapter/file reference
            if (cleanedItemText.includes('.md') || cleanedItemText.match(/^\d+/)) {
              // Format as chapter entry
              const chapterTitle = cleanedItemText
                .replace(/\.md.*$/, '') // Remove .md extension and anything after
                .replace(/^\d+[\s_]*/, '') // Remove leading numbers
                .replace(/[_-]+/g, ' ') // Replace underscores and dashes with spaces
                .trim();
              
              listItems.push(
                <li key={listItems.length} className="mb-3 flex items-start">
                  <span className="inline-block w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                  <span className="text-gray-800 dark:text-gray-200 font-medium hover:text-blue-600 dark:hover:text-blue-400 cursor-pointer transition-colors">
                    {chapterTitle}
                  </span>
                </li>
              );
            } else {
              // Regular list item
              listItems.push(
                <li key={listItems.length} className="mb-2 flex items-start">
                  <span className="inline-block w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full mt-2.5 mr-3 flex-shrink-0"></span>
                  <span className="text-gray-700 dark:text-gray-300">
                    {processInlineMarkdown(cleanedItemText)}
                  </span>
                </li>
              );
            }
            i++;
          } else {
            break; // Exit loop if not a list item
          }
        }
        
        const ListTag = isOrdered ? 'ol' : 'ul';
        const listClass = isOrdered ? 'list-decimal list-inside mb-4 space-y-1' : 'list-disc list-inside mb-4 space-y-1';
        
        elements.push(
          React.createElement(ListTag, {
            key: elements.length,
            className: listClass
          }, listItems)
        );
        continue;
      }

      // Inline code blocks (single backticks)
      if (line.includes('`') && !line.trim().startsWith('```')) {
        elements.push(
          <p key={elements.length} className="mb-4 text-gray-700 dark:text-gray-300 leading-relaxed">
            {processInlineMarkdown(line)}
          </p>
        );
        i++;
        continue;
      }

      // Regular paragraphs
      if (line.trim() !== '') {
        elements.push(
          <p key={elements.length} className="mb-4 text-gray-700 dark:text-gray-300 leading-relaxed">
            {processInlineMarkdown(line)}
          </p>
        );
      }
      
      i++;
    }

    return elements;
  };

  const processInlineMarkdown = (text) => {
    if (!text) return text;

    // Process inline code first
    const parts = text.split(/(`[^`]+`)/);
    const processedParts = parts.map((part, index) => {
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <CodeBlock key={index}>
            {part.slice(1, -1)}
          </CodeBlock>
        );
      }

      // Process other inline formatting
      let processed = part;
      
      // Bold (**text**)
      processed = processed.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      
      // Italic (*text*)
      processed = processed.replace(/\*([^*]+)\*/g, '<em>$1</em>');
      
      // Links [text](url)
      processed = processed.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">$1</a>');

      return <span key={index} dangerouslySetInnerHTML={{ __html: processed }} />;
    });

    return processedParts;
  };

  return (
    <div className="prose prose-gray max-w-none">
      {processMarkdown(content)}
    </div>
  );
};

export default MarkdownRenderer;
