<template>
  <div>
    <NavBar v-if="isAuthenticated" />

    <!-- Page with fade transition -->
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" class="page-content" />
      </transition>
    </router-view>

    <!-- Mobile bottom navigation -->
    <nav v-if="isAuthenticated" class="mobile-bottom-nav">
      <!-- Admin -->
      <template v-if="isAdmin">
        <router-link to="/admin/dashboard"><i class="bi bi-grid-fill"></i>Dashboard</router-link>
        <router-link to="/admin/companies"><i class="bi bi-building"></i>Companies</router-link>
        <router-link to="/admin/students"><i class="bi bi-people-fill"></i>Students</router-link>
        <router-link to="/admin/drives"><i class="bi bi-briefcase-fill"></i>Drives</router-link>
        <router-link to="/admin/jobs"><i class="bi bi-gear-fill"></i>Jobs</router-link>
      </template>
      <!-- Company -->
      <template v-else-if="isCompany">
        <router-link to="/company/dashboard"><i class="bi bi-grid-fill"></i>Dashboard</router-link>
        <router-link to="/company/drives"><i class="bi bi-briefcase-fill"></i>Drives</router-link>
        <router-link to="/company/placements"><i class="bi bi-check-circle-fill"></i>Selected</router-link>
      </template>
      <!-- Student -->
      <template v-else-if="isStudent">
        <router-link to="/student/dashboard"><i class="bi bi-grid-fill"></i>Dashboard</router-link>
        <router-link to="/student/drives"><i class="bi bi-search"></i>Drives</router-link>
        <router-link to="/student/applications"><i class="bi bi-file-earmark-text"></i>Apps</router-link>
        <router-link to="/student/interviews"><i class="bi bi-calendar-event"></i>Interviews</router-link>
        <router-link to="/student/profile"><i class="bi bi-person-fill"></i>Profile</router-link>
      </template>
    </nav>
  </div>
</template>

<script>
import NavBar from './components/NavBar.vue'
import { mapGetters } from 'vuex'

export default {
  name: 'App',
  components: { NavBar },
  computed: {
    ...mapGetters(['isAuthenticated', 'isAdmin', 'isCompany', 'isStudent']),
  },
}
</script>
