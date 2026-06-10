import { create } from 'zustand';

/** UI holati (server holati TanStack Query da) */
interface AddSourceState {
  text: string;
  setText: (t: string) => void;
  clear: () => void;
}

export const useAddSourceStore = create<AddSourceState>((set) => ({
  text: '',
  setText: (text) => set({ text }),
  clear: () => set({ text: '' }),
}));
