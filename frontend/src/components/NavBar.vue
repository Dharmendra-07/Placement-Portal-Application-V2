<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
    <div class="container-fluid px-4">
      <span class="navbar-brand fw-bold">🎓 Placement Portal</span>

      <button class="navbar-toggler" type="button" data-bs-toggle="collapse"
              data-bs-target="#navMenu">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navMenu">
        <!-- Admin links -->
        <ul v-if="isAdmin" class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link to="/admin/dashboard" class="nav-link">Dashboard</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/admin/companies" class="nav-link">Companies</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/admin/students" class="nav-link">Students</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/admin/drives" class="nav-link">Drives</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/admin/applications" class="nav-link">Applications</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/admin/jobs" class="nav-link">Jobs</router-link>
          </li>
        </ul>

        <!-- Company links -->
        <ul v-else-if="isCompany" class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link to="/company/dashboard" class="nav-link">Dashboard</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/company/drives" class="nav-link">My Drives</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/company/placements" class="nav-link">Selected</router-link>
          </li>
        </ul>

        <!-- Student links -->
        <ul v-else-if="isStudent" class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link to="/student/dashboard" class="nav-link">Dashboard</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/student/drives" class="nav-link">Drives</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/student/applications" class="nav-link">Applications</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/student/interviews" class="nav-link">Interviews</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/student/placements" class="nav-link">Placements</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/student/history" class="nav-link">History</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/student/profile" class="nav-link">Profile</router-link>
          </li>
        </ul>

        <!-- Right side: user info + logout -->
        <ul class="navbar-nav ms-auto align-items-center">
          <li class="nav-item me-2">
            <span class="badge bg-light text-primary fw-semibold text-capitalize">
              {{ role }}
            </span>
          </li>
          <li class="nav-item">
            <button class="btn btn-outline-light btn-sm" @click="handleLogout">
              Logout
            </button>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'NavBar',
  computed: {
    ...mapGetters(['isAdmin', 'isCompany', 'isStudent', 'role']),
  },
  methods: {
    ...mapActions(['logout']),
    handleLogout() {
      this.logout()
      this.$router.push('/login')
    },
  },
}
</script>
