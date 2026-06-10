import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { adminFetch, setToken } from '@/shared/api/client';
import { Button, Card, Input } from '@/shared/ui';

import { useAuthStore, type Role } from '../model/store';

const schema = z.object({
  email: z.string().email('Email noto\'g\'ri'),
  password: z.string().min(8, 'Kamida 8 belgi'),
  totp_code: z.string().length(6, '6 raqamli TOTP kod'),
});

type FormData = z.infer<typeof schema>;

function decodeRole(token: string): Role {
  try {
    const payload = JSON.parse(atob(token.split('.')[1])) as { role: Role };
    return payload.role;
  } catch {
    return 'content';
  }
}

export function LoginForm() {
  const nav = useNavigate();
  const setRole = useAuthStore((s) => s.setRole);
  const {
    register, handleSubmit, setError,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    try {
      const res = await adminFetch<{ access_token: string }>('/api/v1/admin/login', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      setToken(res.access_token);
      setRole(decodeRole(res.access_token));
      nav('/');
    } catch {
      setError('root', { message: 'Kirish rad etildi. Ma\'lumotlarni tekshiring.' });
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-96">
        <h1 className="mb-5 text-lg font-semibold">ManbaAI Admin</h1>
        <form className="space-y-3" onSubmit={handleSubmit(onSubmit)}>
          <div>
            <Input placeholder="Email" type="email" {...register('email')} />
            {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
          </div>
          <div>
            <Input placeholder="Parol" type="password" {...register('password')} />
            {errors.password && (
              <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
            )}
          </div>
          <div>
            <Input placeholder="TOTP kod (authenticator)" maxLength={6} {...register('totp_code')} />
            {errors.totp_code && (
              <p className="mt-1 text-xs text-red-600">{errors.totp_code.message}</p>
            )}
          </div>
          {errors.root && <p className="text-sm text-red-600">{errors.root.message}</p>}
          <Button className="w-full" disabled={isSubmitting}>Kirish</Button>
        </form>
      </Card>
    </div>
  );
}
