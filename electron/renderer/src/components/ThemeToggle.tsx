import { useEffect, useState } from 'react';

const themes = [
  { key: 'coral', label: '珊瑚橙', color: '#ff6b4a' },
  { key: 'teal', label: '科技青', color: '#0ea5a0' },
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
    <div className="inline-flex items-center gap-1 px-1 py-1 rounded-lg border border-gray-200 bg-white">
      {themes.map((item) => (
        <button
          key={item.key}
          onClick={() => handleChange(item.key)}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            theme === item.key
              ? 'bg-gray-100 text-gray-900'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
          }`}
        >
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: item.color }}
          />
          {item.label}
        </button>
      ))}
    </div>
  );
};

export default ThemeToggle;
