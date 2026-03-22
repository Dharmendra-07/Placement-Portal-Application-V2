import { createRouter, createWebHistory } from 'vue-router'
import store from '../store'

// Lazy-loaded views
const Login          = () => import('../views/LoginView.vue')
const RegisterStudent= () => import('../views/RegisterStudentView.vue')
const RegisterCompany= () => import('../views/RegisterCompanyView.vue')

const AdminDashboard  = () => import('../views/admin/DashboardView.vue')
const AdminCompanies  = () => import('../views/admin/CompaniesView.vue')
const AdminStudents   = () => import('../views/admin/StudentsView.vue')
const AdminDrives      = () => import('../views/admin/DrivesView.vue')
const AdminApplications= () => import('../views/admin/ApplicationsView.vue')

const CompanyDashboard= () => import('../views/company/DashboardView.vue')
const CompanyDrives   = () => import('../views/company/DrivesView.vue')
const CompanyApplicants = () => import('../views/company/ApplicantsView.vue')
const CompanyPlacements = () => import('../views/company/PlacementsView.vue')

const StudentDashboard= () => import('../views/student/DashboardView.vue')
const StudentDrives   = () => import('../views/student/DrivesView.vue')
const StudentProfile  = () => import('../views/student/ProfileView.vue')
const StudentHistory  = () => import('../views/student/HistoryView.vue')

const routes = [
  { path: '/',        redirect: '/login' },
  { path: '/login',   component: Login,           meta: { guest: true } },
  { path: '/register/student', component: RegisterStudent, meta: { guest: true } },
  { path: '/register/company', component: RegisterCompany, meta: { guest: true } },

  // Admin
  { path: '/admin/dashboard',  component: AdminDashboard,  meta: { role: 'admin' } },
  { path: '/admin/companies',  component: AdminCompanies,  meta: { role: 'admin' } },
  { path: '/admin/students',   component: AdminStudents,   meta: { role: 'admin' } },
  { path: '/admin/drives',        component: AdminDrives,        meta: { role: 'admin' } },
  { path: '/admin/applications', component: AdminApplications,  meta: { role: 'admin' } },

  // Company
  { path: '/company/dashboard',   component: CompanyDashboard,  meta: { role: 'company' } },
  { path: '/company/drives',      component: CompanyDrives,     meta: { role: 'company' } },
  { path: '/company/applicants/:driveId', component: CompanyApplicants, meta: { role: 'company' } },
  { path: '/company/placements',          component: CompanyPlacements, meta: { role: 'company' } },

  // Student
  { path: '/student/dashboard', component: StudentDashboard, meta: { role: 'student' } },
  { path: '/student/drives',    component: StudentDrives,    meta: { role: 'student' } },
  { path: '/student/profile',   component: StudentProfile,   meta: { role: 'student' } },
  { path: '/student/history',   component: StudentHistory,   meta: { role: 'student' } },

  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard
router.beforeEach((to, _from, next) => {
  const isAuth = store.getters.isAuthenticated
  const role   = store.getters.role

  if (to.meta.guest) {
    // Redirect already-logged-in users to their dashboard
    if (isAuth) return next(`/${role}/dashboard`)
    return next()
  }

  if (to.meta.role) {
    if (!isAuth) return next('/login')
    if (to.meta.role !== role) return next(`/${role}/dashboard`)
  }

  next()
})

export default router
