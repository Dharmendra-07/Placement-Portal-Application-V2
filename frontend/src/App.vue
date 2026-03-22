<template>
  <div>
    <NavBar v-if="isAuthenticated" />
    <router-view />
  </div>
</template>

<script>
import NavBar from './components/NavBar.vue'
import { mapGetters } from 'vuex'

export default {
  name: 'App',
  components: { NavBar },
  computed: {
    ...mapGetters(['isAuthenticated']),
  },
}
</script>
