import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './theme/global.css';

type RootElement = HTMLElement & { _reactRootContainer?: unknown };

const rootElement = document.getElementById('root') as RootElement;

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
