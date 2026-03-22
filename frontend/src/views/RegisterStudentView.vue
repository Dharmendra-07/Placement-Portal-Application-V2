<template>
  <div class="container-fluid min-vh-100 d-flex align-items-center justify-content-center bg-light py-4">
    <div class="card shadow-sm" style="width: 100%; max-width: 520px;">
      <div class="card-body p-4">
        <div class="text-center mb-4">
          <h4 class="fw-bold text-primary mb-1">Student Registration</h4>
          <p class="text-muted small">Create your placement portal account</p>
        </div>

        <div v-if="errorMsg"   class="alert alert-danger  py-2 small">{{ errorMsg }}</div>
        <div v-if="successMsg" class="alert alert-success py-2 small">{{ successMsg }}</div>

        <form @submit.prevent="handleRegister" novalidate>
          <div class="row g-3">
            <div class="col-12">
              <label class="form-label fw-medium">Full Name <span class="text-danger">*</span></label>
              <input v-model="form.full_name" type="text" class="form-control"
                     placeholder="John Doe" required />
            </div>

            <div class="col-md-6">
              <label class="form-label fw-medium">Email <span class="text-danger">*</span></label>
              <input v-model="form.email" type="email" class="form-control"
                     placeholder="you@college.edu" required />
            </div>

            <div class="col-md-6">
              <label class="form-label fw-medium">Password <span class="text-danger">*</span></label>
              <input v-model="form.password" type="password" class="form-control"
                     placeholder="Min. 6 characters" required minlength="6" />
            </div>

            <div class="col-md-6">
              <label class="form-label fw-medium">Roll Number</label>
              <input v-model="form.roll_number" type="text" class="form-control"
                     placeholder="e.g. 21CS001" />
            </div>

            <div class="col-md-6">
              <label class="form-label fw-medium">Phone</label>
              <input v-model="form.phone" type="tel" class="form-control"
                     placeholder="+91 98765 43210" />
            </div>

            <div class="col-md-8">
              <label class="form-label fw-medium">Department / Branch</label>
              <input v-model="form.department" type="text" class="form-control"
                     placeholder="Computer Science and Engineering" />
            </div>

            <div class="col-md-4">
              <label class="form-label fw-medium">Year</label>
              <select v-model="form.year" class="form-select">
                <option value="">Select</option>
                <option v-for="y in [1,2,3,4]" :key="y" :value="y">Year {{ y }}</option>
              </select>
            </div>

            <div class="col-md-4">
              <label class="form-label fw-medium">CGPA</label>
              <input v-model.number="form.cgpa" type="number" class="form-control"
                     step="0.01" min="0" max="10" placeholder="e.g. 8.5" />
            </div>

            <div class="col-md-8">
              <label class="form-label fw-medium">Skills <span class="text-muted small">(comma-separated)</span></label>
              <input v-model="form.skills" type="text" class="form-control"
                     placeholder="Python, React, SQL, Machine Learning" />
            </div>
          </div>

          <button type="submit" class="btn btn-primary w-100 mt-4" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            {{ loading ? 'Registering...' : 'Create Account' }}
          </button>
        </form>

        <div class="text-center mt-3 small text-muted">
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
  name: 'RegisterStudentView',
  data() {
    return {
      form: {
        full_name: '', email: '', password: '',
        roll_number: '', phone: '', department: '',
        year: '', cgpa: '', skills: '',
      },
      loading:    false,
      errorMsg:   '',
      successMsg: '',
    }
  },
  methods: {
    ...mapActions(['registerStudent']),
    async handleRegister() {
      this.errorMsg   = ''
      this.successMsg = ''

      if (!this.form.full_name || !this.form.email || !this.form.password) {
        this.errorMsg = 'Full name, email, and password are required.'
        return
      }
      if (this.form.password.length < 6) {
        this.errorMsg = 'Password must be at least 6 characters.'
        return
      }

      this.loading = true
      try {
        await this.registerStudent(this.form)
        this.$router.push('/student/dashboard')
      } catch (err) {
        this.errorMsg = err.response?.data?.message || 'Registration failed.'
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
