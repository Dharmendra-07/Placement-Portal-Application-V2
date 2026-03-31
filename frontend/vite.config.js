import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:5000', changeOrigin: true },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Code-split by route for faster loads
        manualChunks: {
          'vendor':  ['vue', 'vue-router', 'vuex', 'axios'],
          'admin':   [
            './src/views/admin/DashboardView.vue',
            './src/views/admin/CompaniesView.vue',
            './src/views/admin/StudentsView.vue',
            './src/views/admin/DrivesView.vue',
            './src/views/admin/ApplicationsView.vue',
            './src/views/admin/JobsView.vue',
          ],
          'company': [
            './src/views/company/DashboardView.vue',
            './src/views/company/DrivesView.vue',
            './src/views/company/ApplicantsView.vue',
            './src/views/company/PlacementsView.vue',
          ],
          'student': [
            './src/views/student/DashboardView.vue',
            './src/views/student/DrivesView.vue',
            './src/views/student/ApplicationsView.vue',
            './src/views/student/HistoryView.vue',
            './src/views/student/InterviewsView.vue',
            './src/views/student/PlacementsView.vue',
            './src/views/student/ProfileView.vue',
          ],
        },
      },
    },
  },
})
