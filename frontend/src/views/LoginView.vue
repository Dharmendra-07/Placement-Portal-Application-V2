<template>
  <div class="container-fluid min-vh-100 d-flex align-items-center justify-content-center bg-light">
    <div class="card shadow-sm" style="width: 100%; max-width: 420px;">
      <div class="card-body p-4">
        <div class="text-center mb-4">
          <h4 class="fw-bold text-primary mb-1">Placement Portal</h4>
          <p class="text-muted small">Sign in to your account</p>
        </div>

        <div v-if="errorMsg" class="alert alert-danger py-2 small">{{ errorMsg }}</div>

        <form @submit.prevent="handleLogin" novalidate>
          <div class="mb-3">
            <label class="form-label fw-medium">Email address</label>
            <input v-model="form.email" type="email" class="form-control"
                   placeholder="you@example.com" required />
          </div>
          <div class="mb-3">
            <label class="form-label fw-medium">Password</label>
            <div class="input-group">
              <input v-model="form.password" :type="showPwd ? 'text' : 'password'"
                     class="form-control" placeholder="••••••••" required />
              <button class="btn btn-outline-secondary" type="button"
                      @click="showPwd = !showPwd">
                {{ showPwd ? 'Hide' : 'Show' }}
              </button>
            </div>
          </div>

          <button type="submit" class="btn btn-primary w-100" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            {{ loading ? 'Signing in...' : 'Sign in' }}
          </button>
        </form>

        <hr class="my-3" />
        <div class="text-center small text-muted">
          Don't have an account?
          <router-link to="/register/student" class="text-decoration-none">Register as Student</router-link>
          &nbsp;|&nbsp;
          <router-link to="/register/company" class="text-decoration-none">Register as Company</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'

export default {
  name: 'LoginView',
  data() {
    return {
      form:     { email: '', password: '' },
      loading:  false,
      showPwd:  false,
      errorMsg: '',
    }
  },
  methods: {
    ...mapActions(['login']),
    async handleLogin() {
      this.errorMsg = ''
      if (!this.form.email || !this.form.password) {
        this.errorMsg = 'Please enter your email and password.'
        return
      }
      this.loading = true
      try {
        const role = await this.login(this.form)
        this.$router.push(`/${role}/dashboard`)
      } catch (err) {
        this.errorMsg = err.response?.data?.message || 'Login failed. Please try again.'
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
