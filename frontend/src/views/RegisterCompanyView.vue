<template>
  <div class="container-fluid min-vh-100 d-flex align-items-center justify-content-center bg-light py-4">
    <div class="card shadow-sm" style="width: 100%; max-width: 520px;">
      <div class="card-body p-4">
        <div class="text-center mb-4">
          <h4 class="fw-bold text-primary mb-1">Company Registration</h4>
          <p class="text-muted small">Register your company — pending admin approval</p>
        </div>

        <div v-if="errorMsg"   class="alert alert-danger  py-2 small">{{ errorMsg }}</div>

        <!-- Success state: pending approval -->
        <div v-if="registered" class="text-center py-3">
          <div class="mb-3" style="font-size:3rem">✅</div>
          <h5 class="fw-bold">Registration Submitted!</h5>
          <p class="text-muted small">
            Your company profile is pending admin approval.<br>
            You will be able to log in once approved.
          </p>
          <router-link to="/login" class="btn btn-primary">Back to Login</router-link>
        </div>

        <form v-else @submit.prevent="handleRegister" novalidate>
          <div class="row g-3">
            <div class="col-12">
              <label class="form-label fw-medium">Company Name <span class="text-danger">*</span></label>
              <input v-model="form.name" type="text" class="form-control"
                     placeholder="Acme Corp" required />
            </div>

            <div class="col-md-6">
              <label class="form-label fw-medium">Email <span class="text-danger">*</span></label>
              <input v-model="form.email" type="email" class="form-control"
                     placeholder="hr@company.com" required />
            </div>

            <div class="col-md-6">
              <label class="form-label fw-medium">Password <span class="text-danger">*</span></label>
              <input v-model="form.password" type="password" class="form-control"
                     placeholder="Min. 6 characters" required minlength="6" />
            </div>

            <div class="col-md-6">
              <label class="form-label fw-medium">Industry</label>
              <input v-model="form.industry" type="text" class="form-control"
                     placeholder="Information Technology" />
            </div>

            <div class="col-md-6">
              <label class="form-label fw-medium">Location</label>
              <input v-model="form.location" type="text" class="form-control"
                     placeholder="Bengaluru, India" />
            </div>

            <div class="col-md-6">
              <label class="form-label fw-medium">Website</label>
              <input v-model="form.website" type="url" class="form-control"
                     placeholder="https://company.com" />
            </div>

            <div class="col-md-6">
              <label class="form-label fw-medium">HR Contact Name</label>
              <input v-model="form.hr_contact_name" type="text" class="form-control"
                     placeholder="Jane Smith" />
            </div>

            <div class="col-md-6">
              <label class="form-label fw-medium">HR Contact Phone</label>
              <input v-model="form.hr_contact_phone" type="tel" class="form-control"
                     placeholder="+91 98765 43210" />
            </div>

            <div class="col-12">
              <label class="form-label fw-medium">Company Description</label>
              <textarea v-model="form.description" class="form-control" rows="3"
                        placeholder="Brief overview of your company..."></textarea>
            </div>
          </div>

          <button type="submit" class="btn btn-primary w-100 mt-4" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            {{ loading ? 'Submitting...' : 'Submit for Approval' }}
          </button>
        </form>

        <div v-if="!registered" class="text-center mt-3 small text-muted">
          Already have an account?
          <router-link to="/login" class="text-decoration-none">Sign in</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'

export default {
  name: 'RegisterCompanyView',
  data() {
    return {
      form: {
        name: '', email: '', password: '',
        industry: '', location: '', website: '',
        hr_contact_name: '', hr_contact_phone: '', description: '',
      },
      loading:    false,
      errorMsg:   '',
      registered: false,
    }
  },
  methods: {
    ...mapActions(['registerCompany']),
    async handleRegister() {
      this.errorMsg = ''
      if (!this.form.name || !this.form.email || !this.form.password) {
        this.errorMsg = 'Company name, email, and password are required.'
        return
      }
      if (this.form.password.length < 6) {
        this.errorMsg = 'Password must be at least 6 characters.'
        return
      }
      this.loading = true
      try {
        await this.registerCompany(this.form)
        this.registered = true
      } catch (err) {
        this.errorMsg = err.response?.data?.message || 'Registration failed.'
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
