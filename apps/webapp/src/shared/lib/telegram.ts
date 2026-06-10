/** Telegram WebApp API o'rami: tema, haptic, tugmalar. */
type TgWebApp = {
  initData: string;
  colorScheme: 'light' | 'dark';
  ready: () => void;
  expand: () => void;
  BackButton: { show: () => void; hide: () => void; onClick: (cb: () => void) => void };
  MainButton: {
    setText: (t: string) => void; show: () => void; hide: () => void;
    onClick: (cb: () => void) => void; offClick: (cb: () => void) => void;
  };
  HapticFeedback: { impactOccurred: (s: 'light' | 'medium' | 'heavy') => void };
};

export const tg = (): TgWebApp | undefined =>
  (window as unknown as { Telegram?: { WebApp?: TgWebApp } }).Telegram?.WebApp;

export const initData = (): string => tg()?.initData ?? '';
export const haptic = (style: 'light' | 'medium' | 'heavy' = 'light'): void =>
  tg()?.HapticFeedback.impactOccurred(style);
