import { useEffect, useState } from 'react';

const themes = [
  { key: 'purple', label: '紫罗兰', emoji: '🌌' },
  { key: 'pink', label: '猫爪粉', emoji: '🌸' },
];

const ThemeToggle = () => {
  const [theme, setTheme] = useState<string>('purple');

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
    <div className="inline-flex bg-white/70 backdrop-blur px-2 py-1 rounded-full shadow border border-white/50">
      {themes.map((item) => (
        <button
          key={item.key}
          onClick={() => handleChange(item.key)}
          className={`px-3 py-1 rounded-full text-sm font-medium transition-all ${
            theme === item.key
              ? 'bg-gradient-to-r from-purple-400 to-pink-400 text-white shadow'
              : 'text-slate-500 hover:text-purple-500'
          }`}
        >
          <span className="mr-1">{item.emoji}</span>
          {item.label}
        </button>
      ))}
    </div>
  );
};

export default ThemeToggle;
