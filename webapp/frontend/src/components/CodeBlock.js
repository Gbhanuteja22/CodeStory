import React from 'react';
import { Copy, Check } from 'lucide-react';

const CodeBlock = ({ children, className = '', language = '' }) => {
  const [copied, setCopied] = React.useState(false);
  const codeRef = React.useRef(null);

  const extractCodeText = (element) => {
    if (typeof element === 'string') {
      return element;
    }
    if (Array.isArray(element)) {
      return element.map(extractCodeText).join('');
    }
    if (element && element.props && element.props.children) {
      return extractCodeText(element.props.children);
    }
    return '';
  };

  const copyToClipboard = async () => {
    try {
      let textToCopy = '';
      
      if (codeRef.current) {
        // Try to get text content from the DOM element
        textToCopy = codeRef.current.textContent || codeRef.current.innerText || '';
      }
      
      // Fallback: extract from React children
      if (!textToCopy && children) {
        textToCopy = extractCodeText(children);
      }
      
      if (textToCopy) {
        await navigator.clipboard.writeText(textToCopy);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    } catch (err) {
      console.error('Failed to copy code:', err);
      // Fallback for older browsers
      try {
        const textArea = document.createElement('textarea');
        textArea.value = extractCodeText(children);
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (fallbackErr) {
        console.error('Fallback copy also failed:', fallbackErr);
      }
    }
  };

  const isCodeBlock = className?.includes('language-') || language;

  if (!isCodeBlock) {
    // Regular inline code with better dark/light theme contrast
    return (
      <code className="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-2 py-1 rounded border border-gray-200 dark:border-gray-700 text-sm font-mono shadow-sm">
        {children}
      </code>
    );
  }

  // Block code with copy functionality and enhanced dark/light theme styling
  return (
    <div className="relative group my-4">
      <pre className={`bg-gray-900 dark:bg-gray-950 text-gray-100 dark:text-gray-50 p-4 rounded-lg overflow-x-auto border border-gray-700 dark:border-gray-600 shadow-lg ${className}`}>
        <code ref={codeRef} className="font-mono text-sm leading-relaxed">
          {children}
        </code>
      </pre>
      
      {/* Copy Button */}
      <button
        onClick={copyToClipboard}
        className={`absolute top-2 right-2 p-2 rounded-md transition-all duration-200 ${
          copied 
            ? 'bg-green-600 dark:bg-green-500 text-white' 
            : 'bg-gray-700 dark:bg-gray-800 text-gray-300 dark:text-gray-200 hover:bg-gray-600 dark:hover:bg-gray-700 opacity-0 group-hover:opacity-100'
        }`}
        title={copied ? 'Copied!' : 'Copy code'}
      >
        {copied ? (
          <Check className="w-4 h-4" />
        ) : (
          <Copy className="w-4 h-4" />
        )}
      </button>
      
      {/* Copy Success Tooltip */}
      {copied && (
        <div className="absolute top-12 right-2 bg-green-600 dark:bg-green-500 text-white text-xs px-2 py-1 rounded shadow-lg">
          Copied!
        </div>
      )}
    </div>
  );
};

export default CodeBlock;
