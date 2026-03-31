<template>
  <div class="min-vh-100 d-flex align-items-center justify-content-center"
       style="background:linear-gradient(135deg,#e8f0fe 0%,#f8f9fc 100%)">
    <div class="card border-0" style="width:100%;max-width:420px;">
      <div class="card-body p-4 p-md-5">

        <!-- Logo / brand -->
        <div class="text-center mb-4">
          <div class="d-inline-flex align-items-center justify-content-center
                      rounded-3 mb-3"
               style="width:52px;height:52px;background:#0d6efd">
            <i class="bi bi-mortarboard-fill text-white fs-4"></i>
          </div>
          <h5 class="fw-bold mb-1">Placement Portal</h5>
          <p class="text-muted small">Sign in to your account</p>
        </div>

        <div v-if="errorMsg" class="alert alert-danger py-2 small d-flex gap-2">
          <i class="bi bi-exclamation-triangle-fill"></i> {{ errorMsg }}
        </div>

        <form @submit.prevent="handleLogin" novalidate>
          <div class="mb-3">
            <label class="form-label">Email address</label>
            <div class="input-group">
              <span class="input-group-text bg-light border-end-0">
                <i class="bi bi-envelope text-muted"></i>
              </span>
              <input v-model.trim="form.email" type="email"
                     :class="['form-control border-start-0',
                               errors.email ? 'is-invalid' : '']"
                     placeholder="you@example.com"
                     @blur="touchField('email')" />
              <div class="invalid-feedback">{{ errors.email }}</div>
            </div>
          </div>

          <div class="mb-4">
            <label class="form-label">Password</label>
            <div class="input-group">
              <span class="input-group-text bg-light border-end-0">
                <i class="bi bi-lock text-muted"></i>
              </span>
              <input v-model="form.password"
                     :type="showPwd ? 'text' : 'password'"
                     :class="['form-control border-start-0 border-end-0',
                               errors.password ? 'is-invalid' : '']"
                     placeholder="••••••••"
                     @blur="touchField('password')" />
              <button class="btn btn-outline-secondary border-start-0" type="button"
                      @click="showPwd = !showPwd" tabindex="-1">
                <i :class="showPwd ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
              </button>
              <div class="invalid-feedback">{{ errors.password }}</div>
            </div>
          </div>

          <button type="submit" class="btn btn-primary w-100 py-2" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            {{ loading ? 'Signing in…' : 'Sign in' }}
          </button>
        </form>

        <hr class="my-3" />
        <p class="text-center text-muted small mb-0">
          No account?
          <router-link to="/register/student" class="text-decoration-none fw-medium">
            Register as Student
          </router-link>
          &nbsp;·&nbsp;
          <router-link to="/register/company" class="text-decoration-none fw-medium">
            Register as Company
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import { v, validate } from '../utils/validators'

export default {
  name: 'LoginView',
  data() {
    return {
      form:     { email: '', password: '' },
      errors:   {},
      loading:  false,
      showPwd:  false,
      errorMsg: '',
    }
  },
  methods: {
    ...mapActions(['login']),
    touchField(field) {
      const { errors } = validate(this.form, {
        email:    [[v.required, 'Email'],    [v.email]],
        password: [[v.required, 'Password'], [v.minLength, 6, 'Password']],
      })
      if (errors[field]) this.errors = { ...this.errors, [field]: errors[field] }
      else               delete this.errors[field]
    },
    async handleLogin() {
      this.errorMsg = ''
      const { errors, valid } = validate(this.form, {
        email:    [[v.required, 'Email'],    [v.email]],
        password: [[v.required, 'Password'], [v.minLength, 6, 'Password']],
      })
      this.errors = errors
      if (!valid) return
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
