import React from 'react';
import { termsOfService } from '../data/terms-of-service';
import { privacyPolicy } from '../data/privacy-policy';

interface TermsModalProps {
  isOpen: boolean;
  onClose: () => void;
  type: 'terms' | 'privacy';
}

const TermsModal: React.FC<TermsModalProps> = ({ isOpen, onClose, type }) => {
  if (!isOpen) return null;

  const content = type === 'terms' ? termsOfService : privacyPolicy;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col sm:max-w-lg md:max-w-2xl lg:max-w-4xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200">
          <div>
            <h2 className="text-lg sm:text-2xl font-semibold text-gray-900">{content.title}</h2>
            <p className="text-xs sm:text-sm text-gray-500 mt-1">
              最后更新：{content.lastUpdated} | 版本：{content.version}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors p-2 rounded-full hover:bg-gray-100"
            aria-label="关闭"
          >
            <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
          <div 
            className="prose prose-sm max-w-none text-gray-700 leading-relaxed"
            style={{ fontSize: '12px', lineHeight: '1.6' }}
            dangerouslySetInnerHTML={{ 
              __html: content.content
                .replace(/\n/g, '<br>')
                .replace(/#{1,6}\s(.+)/g, (match, title) => {
                  const level = match.indexOf(' ') - 1;
                  const className = level === 1 ? 'text-base sm:text-xl font-bold text-gray-900 mt-4 sm:mt-6 mb-3 sm:mb-4' :
                                   level === 2 ? 'text-sm sm:text-lg font-semibold text-gray-800 mt-3 sm:mt-5 mb-2 sm:mb-3' :
                                   'text-sm sm:text-base font-medium text-gray-800 mt-2 sm:mt-4 mb-1 sm:mb-2';
                  return `<h${level} class="${className}">${title}</h${level}>`;
                })
                .replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
                .replace(/- (.+)/g, '<li class="ml-4 mb-1 text-xs sm:text-sm">$1</li>')
                .replace(/(\d+\.\d+)\s(.+)/g, '<h4 class="font-medium text-gray-800 mt-2 sm:mt-3 mb-1 sm:mb-2 text-xs sm:text-sm">$1 $2</h4>')
            }}
          />
        </div>

        {/* Footer */}
        <div className="flex justify-end p-4 sm:p-6 border-t border-gray-200 bg-gray-50 rounded-b-2xl">
          <button
            onClick={onClose}
            className="px-4 sm:px-6 py-2 bg-purple-500 text-white rounded-xl hover:bg-purple-600 transition-colors font-medium text-sm sm:text-base"
          >
            我已阅读
          </button>
        </div>
      </div>
    </div>
  );
};

export default TermsModal;