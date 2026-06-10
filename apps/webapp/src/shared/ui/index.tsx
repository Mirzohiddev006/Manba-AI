import type { ButtonHTMLAttributes, ReactNode } from 'react';

export function Button({
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={`rounded-xl bg-tg-button px-4 py-2.5 font-medium text-tg-buttonText
        active:opacity-80 disabled:opacity-40 ${className}`}
      {...props}
    />
  );
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl bg-tg-secondary p-4 ${className}`}>{children}</div>
  );
}

export function Spinner() {
  return (
    <div className="flex justify-center p-8">
      <div className="h-7 w-7 animate-spin rounded-full border-2 border-tg-button border-t-transparent" />
    </div>
  );
}

export function EmptyState({ text }: { text: string }) {
  return <p className="p-8 text-center text-tg-hint">{text}</p>;
}
