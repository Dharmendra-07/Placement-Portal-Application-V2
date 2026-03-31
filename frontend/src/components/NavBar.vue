<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary sticky-top">
    <div class="container-fluid px-3 px-md-4">

      <!-- Brand -->
      <router-link class="navbar-brand d-flex align-items-center gap-2"
                   :to="`/${role}/dashboard`">
        <i class="bi bi-mortarboard-fill"></i>
        <span class="d-none d-sm-inline">PPA</span>
      </router-link>

      <!-- Mobile: user badge + toggler -->
      <div class="d-flex align-items-center gap-2 d-lg-none ms-auto">
        <span class="badge bg-white text-primary fw-semibold text-capitalize">
          {{ role }}
        </span>
        <button class="navbar-toggler border-0" type="button"
                data-bs-toggle="collapse" data-bs-target="#navMenu">
          <span class="navbar-toggler-icon"></span>
        </button>
      </div>

      <!-- Collapsible nav -->
      <div class="collapse navbar-collapse" id="navMenu">
        <!-- Admin links -->
        <ul v-if="isAdmin" class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link to="/admin/dashboard" class="nav-link">
              <i class="bi bi-grid me-1"></i>Dashboard
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/admin/companies" class="nav-link">
              <i class="bi bi-building me-1"></i>Companies
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/admin/students" class="nav-link">
              <i class="bi bi-people me-1"></i>Students
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/admin/drives" class="nav-link">
              <i class="bi bi-briefcase me-1"></i>Drives
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/admin/applications" class="nav-link">
              <i class="bi bi-file-earmark-text me-1"></i>Applications
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/admin/jobs" class="nav-link">
              <i class="bi bi-gear me-1"></i>Jobs
            </router-link>
          </li>
        </ul>

        <!-- Company links -->
        <ul v-else-if="isCompany" class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link to="/company/dashboard" class="nav-link">
              <i class="bi bi-grid me-1"></i>Dashboard
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/company/drives" class="nav-link">
              <i class="bi bi-briefcase me-1"></i>My Drives
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/company/placements" class="nav-link">
              <i class="bi bi-check-circle me-1"></i>Selected
            </router-link>
          </li>
        </ul>

        <!-- Student links -->
        <ul v-else-if="isStudent" class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link to="/student/dashboard" class="nav-link">
              <i class="bi bi-grid me-1"></i>Dashboard
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/student/drives" class="nav-link">
              <i class="bi bi-search me-1"></i>Drives
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/student/applications" class="nav-link">
              <i class="bi bi-file-earmark-text me-1"></i>Applications
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/student/interviews" class="nav-link">
              <i class="bi bi-calendar-event me-1"></i>Interviews
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/student/placements" class="nav-link">
              <i class="bi bi-award me-1"></i>Placements
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/student/history" class="nav-link">
              <i class="bi bi-clock-history me-1"></i>History
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/student/profile" class="nav-link">
              <i class="bi bi-person me-1"></i>Profile
            </router-link>
          </li>
        </ul>

        <!-- Right side -->
        <ul class="navbar-nav ms-auto align-items-center">
          <li class="nav-item me-2 d-none d-lg-block">
            <span class="badge bg-white text-primary fw-semibold text-capitalize">
              {{ role }}
            </span>
          </li>
          <li class="nav-item">
            <button class="btn btn-outline-light btn-sm" @click="handleLogout">
              <i class="bi bi-box-arrow-right me-1"></i>Logout
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
