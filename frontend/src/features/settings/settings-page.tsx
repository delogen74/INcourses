import { useState } from 'react';

import { Button, Card, Input, Page } from '../../components/ui';
import { clearApiToken, getApiBaseUrl, getApiToken, setApiToken } from '../../store/settings';

export const SettingsPage = () => {
  const [token, setToken] = useState(getApiToken());
  const [saved, setSaved] = useState(false);

  return (
    <Page>
      <Card className="max-w-2xl">
        <h2 className="mb-4 text-lg font-semibold">Настройки API</h2>

        <div className="mb-4">
          <p className="mb-1 text-xs text-slate-600">API base URL (из env)</p>
          <Input value={getApiBaseUrl()} readOnly />
        </div>

        <div className="mb-3">
          <p className="mb-1 text-xs text-slate-600">API Token (Bearer)</p>
          <Input value={token} onChange={(e) => setToken(e.target.value)} placeholder="Вставьте access token" />
        </div>

        <div className="flex gap-2">
          <Button
            onClick={() => {
              setApiToken(token.trim());
              setSaved(true);
              setTimeout(() => setSaved(false), 2000);
            }}
          >
            Сохранить token
          </Button>
          <Button
            className="bg-slate-600"
            onClick={() => {
              clearApiToken();
              setToken('');
            }}
          >
            Clear token
          </Button>
        </div>

        {saved ? <p className="mt-3 text-sm text-emerald-700">Сохранено.</p> : null}
      </Card>
    </Page>
  );
};
