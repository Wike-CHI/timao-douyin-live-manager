import cloudbase from '@cloudbase/js-sdk';

let cachedApp: ReturnType<typeof cloudbase.init> | null = null;
let cachedEnvId: string | null = null;

export const getCloudBaseApp = (envId: string) => {
  if (!cachedApp || cachedEnvId !== envId) {
    cachedApp = cloudbase.init({ env: envId });
    cachedEnvId = envId;
  }
  return cachedApp;
};

export const getCloudBaseAuth = (envId: string) => {
  const app = getCloudBaseApp(envId);
  return app.auth({ persistence: 'local' });
};

export type CloudBaseAuth = ReturnType<typeof getCloudBaseAuth>;
