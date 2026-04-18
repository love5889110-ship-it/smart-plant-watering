/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  safelist: [
    // 动态背景渐变
    'from-green-600','to-emerald-500','from-green-500','to-emerald-600',
    'from-amber-500','to-orange-500','from-red-600','to-rose-500','from-red-500','to-rose-600',
    'from-blue-500','to-cyan-400','from-blue-400','to-cyan-500',
    'from-blue-600','to-indigo-700','from-blue-700','to-indigo-600',
    'from-gray-500','to-slate-600','from-gray-600','to-slate-500',
    'from-slate-800','to-indigo-900','from-orange-400','to-rose-400',
    'from-orange-500','to-pink-600','from-blue-500','to-cyan-400',
    'from-amber-400','to-orange-500','from-orange-400','to-yellow-400',
    // 背景色
    'bg-green-400','bg-orange-400','bg-red-400','bg-blue-400','bg-indigo-400','bg-gray-400',
  ],
  theme: {
    extend: {}
  },
  plugins: []
}
