export default function Dashboard({ params: { locale } }: { params: { locale: string } }) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      <p className="mt-2 text-gray-500">Onboarding complete ✓</p>
    </main>
  );
}
