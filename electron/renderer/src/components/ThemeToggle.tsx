import { useEffect, useState } from 'react';

const themes = [
  { key: 'mint', label: '薄荷绿', color: '#10b981' },
  { key: 'peach', label: '蜜桃粉', color: '#f472b6' },
  { key: 'coral', label: '珊瑚橙', color: '#f97316' },
  { key: 'dark', label: '暗夜', color: '#fbbf24' },
];

const ThemeToggle = () => {
  const [themeIndex, setThemeIndex] = useState(0);

  useEffect(() => {
    const stored = localStorage.getItem('timao_theme');
    const index = themes.findIndex(t => t.key === stored);
    if (index >= 0) {
      setThemeIndex(index);
      document.body.setAttribute('data-theme', stored);
    } else {
      document.body.setAttribute('data-theme', themes[0].key);
    }
  }, []);

  const handleToggle = () => {
    const nextIndex = (themeIndex + 1) % themes.length;
    setThemeIndex(nextIndex);
    const nextTheme = themes[nextIndex];
    document.body.setAttribute('data-theme', nextTheme.key);
    localStorage.setItem('timao_theme', nextTheme.key);
  };

  const currentTheme = themes[themeIndex];

  return (
    <button
      onClick={handleToggle}
      className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-gray-200/80 bg-white shadow-sm hover:shadow-md transition-all duration-200"
      title={`点击切换配色：${currentTheme.label}`}
    >
      <span
        className="w-3 h-3 rounded-full shadow-sm transition-colors duration-300"
        style={{ backgroundColor: currentTheme.color }}
      />
      <span className="text-sm font-medium text-gray-700">{currentTheme.label}</span>
    </button>
  );
};

export default ThemeToggle;
