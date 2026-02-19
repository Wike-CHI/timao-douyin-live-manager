import { useEffect, useState, useRef, useCallback } from 'react';

const themes = [
  { key: 'mint', label: '薄荷绿', color: '#10b981', desc: '清新专业' },
  { key: 'peach', label: '蜜桃粉', color: '#f472b6', desc: '温暖浪漫' },
  { key: 'coral', label: '珊瑚橙', color: '#f97316', desc: '活力阳光' },
  { key: 'dark', label: '暗夜', color: '#1e293b', desc: '护眼深色' },
];

const ThemeToggle = () => {
  const [theme, setTheme] = useState<string>('mint');
  const [isOpen, setIsOpen] = useState(false);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, right: 0 });
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const stored = localStorage.getItem('timao_theme');
    const nextTheme = stored || theme;
    setTheme(nextTheme);
    document.body.setAttribute('data-theme', nextTheme);
    if (!stored) {
      localStorage.setItem('timao_theme', nextTheme);
    }
  }, []);

  // 更新下拉菜单位置
  const updatePosition = useCallback(() => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + 8,
        right: window.innerWidth - rect.right,
      });
    }
  }, []);

  // 打开时计算位置
  useEffect(() => {
    if (isOpen) {
      updatePosition();
    }
  }, [isOpen, updatePosition]);

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleChange = (value: string) => {
    setTheme(value);
    document.body.setAttribute('data-theme', value);
    localStorage.setItem('timao_theme', value);
    setIsOpen(false);
  };

  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  const currentTheme = themes.find(t => t.key === theme) || themes[0];

  return (
    <div className="relative">
      {/* 当前主题按钮 */}
      <button
        ref={buttonRef}
        onClick={handleToggle}
        className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-gray-200/80 bg-white shadow-sm hover:shadow-md transition-all duration-200"
      >
        <span
          className="w-3 h-3 rounded-full ring-2 ring-white shadow-sm"
          style={{ backgroundColor: currentTheme.color }}
        />
        <span className="text-sm font-medium text-gray-700">{currentTheme.label}</span>
        <svg
          className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* 下拉菜单 - 使用 fixed 定位确保在最上层 */}
      {isOpen && (
        <div
          ref={dropdownRef}
          style={{
            position: 'fixed',
            top: dropdownPosition.top,
            right: dropdownPosition.right,
            width: 200,
            zIndex: 99999,
          }}
          className="py-2 bg-white rounded-xl border border-gray-200 shadow-2xl"
        >
          {themes.map((item) => (
            <button
              key={item.key}
              onClick={() => handleChange(item.key)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-gray-50 transition-colors ${
                theme === item.key ? 'bg-gray-50' : ''
              }`}
            >
              <span
                className="w-4 h-4 rounded-full ring-2 ring-white shadow-sm flex-shrink-0"
                style={{ backgroundColor: item.color }}
              />
              <div className="flex-1 min-w-0">
                <div className={`text-sm font-medium ${theme === item.key ? 'text-gray-900' : 'text-gray-700'}`}>
                  {item.label}
                </div>
                <div className="text-xs text-gray-400">{item.desc}</div>
              </div>
              {theme === item.key && (
                <svg className="w-4 h-4 text-gray-900 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default ThemeToggle;
