/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_FASTAPI_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
