import { useEffect, useState } from 'react';

const themes = [
  { key: 'coral', label: '玫瑰橙', color: '#ff7a5c' },
  { key: 'rose', label: '蜜桃粉', color: '#f472b6' },
  { key: 'dark', label: '暗夜', color: '#1e293b' },
];

const ThemeToggle = () => {
  const [theme, setTheme] = useState<string>('coral');

  useEffect(() => {
    const stored = localStorage.getItem('timao_theme');
    const nextTheme = stored || theme;
    setTheme(nextTheme);
    document.body.setAttribute('data-theme', nextTheme);
    if (!stored) {
      localStorage.setItem('timao_theme', nextTheme);
    }
  }, []);

  const handleChange = (value: string) => {
    setTheme(value);
    document.body.setAttribute('data-theme', value);
    localStorage.setItem('timao_theme', value);
  };

  return (
    <div className="inline-flex items-center gap-0.5 px-1 py-1 rounded-xl border border-gray-200/80 bg-white/90 backdrop-blur-sm shadow-sm">
      {themes.map((item) => (
        <button
          key={item.key}
          onClick={() => handleChange(item.key)}
          className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
            theme === item.key
              ? 'bg-gray-900 text-white shadow-sm'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          <span
            className="w-2 h-2 rounded-full ring-2 ring-offset-1"
            style={{
              backgroundColor: item.color,
              ringColor: theme === item.key ? item.color : 'transparent'
            }}
          />
          {item.label}
        </button>
      ))}
    </div>
  );
};

export default ThemeToggle;
