<template>
  <div class="min-vh-100 d-flex align-items-center justify-content-center py-4"
       style="background:linear-gradient(135deg,#e8f0fe 0%,#f8f9fc 100%)">
    <div class="card border-0" style="width:100%;max-width:560px;">
      <div class="card-body p-4 p-md-5">
        <div class="text-center mb-4">
          <div class="d-inline-flex align-items-center justify-content-center
                      rounded-3 mb-3"
               style="width:52px;height:52px;background:#198754">
            <i class="bi bi-person-plus-fill text-white fs-4"></i>
          </div>
          <h5 class="fw-bold mb-1">Student Registration</h5>
          <p class="text-muted small">Create your placement portal account</p>
        </div>

        <div v-if="errorMsg" class="alert alert-danger py-2 small d-flex gap-2">
          <i class="bi bi-exclamation-triangle-fill"></i> {{ errorMsg }}
        </div>

        <form @submit.prevent="handleRegister" novalidate>
          <div class="row g-3">
            <div class="col-12">
              <label class="form-label">Full Name <span class="text-danger">*</span></label>
              <input v-model.trim="form.full_name" type="text"
                     :class="fieldClass('full_name')"
                     placeholder="John Doe"
                     @blur="touch('full_name')" />
              <div class="invalid-feedback">{{ errors.full_name }}</div>
            </div>

            <div class="col-md-6">
              <label class="form-label">Email <span class="text-danger">*</span></label>
              <input v-model.trim="form.email" type="email"
                     :class="fieldClass('email')"
                     placeholder="you@college.edu"
                     @blur="touch('email')" />
              <div class="invalid-feedback">{{ errors.email }}</div>
            </div>

            <div class="col-md-6">
              <label class="form-label">Password <span class="text-danger">*</span></label>
              <div class="input-group">
                <input v-model="form.password"
                       :type="showPwd ? 'text' : 'password'"
                       :class="['form-control border-end-0', errors.password ? 'is-invalid' : '']"
                       placeholder="Min. 6 characters"
                       @blur="touch('password')" />
                <button class="btn btn-outline-secondary border-start-0" type="button"
                        @click="showPwd = !showPwd" tabindex="-1">
                  <i :class="showPwd ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
                </button>
                <div class="invalid-feedback">{{ errors.password }}</div>
              </div>
            </div>

            <div class="col-md-6">
              <label class="form-label">Roll Number</label>
              <input v-model.trim="form.roll_number" type="text"
                     class="form-control" placeholder="21CS001" />
            </div>

            <div class="col-md-6">
              <label class="form-label">Phone</label>
              <input v-model.trim="form.phone" type="tel"
                     :class="fieldClass('phone')"
                     placeholder="+91 98765 43210"
                     @blur="touch('phone')" />
              <div class="invalid-feedback">{{ errors.phone }}</div>
            </div>

            <div class="col-md-7">
              <label class="form-label">Department / Branch</label>
              <input v-model.trim="form.department" type="text"
                     class="form-control" placeholder="Computer Science and Engineering" />
            </div>

            <div class="col-md-2">
              <label class="form-label">Year</label>
              <select v-model.number="form.year" class="form-select">
                <option value="">—</option>
                <option v-for="y in [1,2,3,4]" :key="y" :value="y">{{ y }}</option>
              </select>
            </div>

            <div class="col-md-3">
              <label class="form-label">CGPA</label>
              <input v-model.number="form.cgpa" type="number"
                     :class="fieldClass('cgpa')"
                     step="0.01" min="0" max="10" placeholder="8.5"
                     @blur="touch('cgpa')" />
              <div class="invalid-feedback">{{ errors.cgpa }}</div>
            </div>

            <div class="col-12">
              <label class="form-label">
                Skills <span class="text-muted small">(comma-separated)</span>
              </label>
              <input v-model.trim="form.skills" type="text"
                     class="form-control"
                     placeholder="Python, React, SQL, Machine Learning" />
              <div v-if="skillChips.length" class="d-flex flex-wrap gap-1 mt-2">
                <span v-for="sk in skillChips" :key="sk"
                      class="badge bg-light text-secondary border">{{ sk }}</span>
              </div>
            </div>
          </div>

          <!-- Progress indicator -->
          <div class="d-flex align-items-center gap-2 mt-3 mb-1">
            <div class="progress flex-grow-1" style="height:4px">
              <div class="progress-bar bg-success"
                   :style="`width:${formProgress}%`"></div>
            </div>
            <span class="text-muted small">{{ formProgress }}% complete</span>
          </div>

          <button type="submit" class="btn btn-success w-100 py-2 mt-2"
                  :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            {{ loading ? 'Creating account…' : 'Create Account' }}
          </button>
        </form>

        <p class="text-center mt-3 text-muted small mb-0">
          Already have an account?
          <router-link to="/login" class="text-decoration-none fw-medium">Sign in</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import { v, validate } from '../utils/validators'

const RULES = {
  full_name: [[v.required, 'Full name'], [v.minLength, 2, 'Full name']],
  email:     [[v.required, 'Email'],    [v.email]],
  password:  [[v.required, 'Password'], [v.minLength, 6, 'Password']],
  phone:     [[v.phone]],
  cgpa:      [[v.cgpa]],
}

export default {
  name: 'RegisterStudentView',
  data() {
    return {
      form: {
        full_name: '', email: '', password: '', roll_number: '',
        phone: '', department: '', year: '', cgpa: '', skills: '',
      },
      errors: {}, loading: false, showPwd: false, errorMsg: '',
    }
  },
  computed: {
    skillChips() {
      return this.form.skills
        ? this.form.skills.split(',').map(s => s.trim()).filter(Boolean)
        : []
    },
    formProgress() {
      const fields = ['full_name', 'email', 'password', 'roll_number',
                      'department', 'year', 'cgpa', 'skills']
      const filled = fields.filter(f => String(this.form[f] || '').trim() !== '').length
      return Math.round(filled / fields.length * 100)
    },
  },
  methods: {
    ...mapActions(['registerStudent']),
    fieldClass(field) {
      return ['form-control', this.errors[field] ? 'is-invalid' : '']
    },
    touch(field) {
      const { errors } = validate(this.form, { [field]: RULES[field] || [] })
      if (errors[field]) this.errors = { ...this.errors, [field]: errors[field] }
      else { const e = { ...this.errors }; delete e[field]; this.errors = e }
    },
    async handleRegister() {
      this.errorMsg = ''
      const { errors, valid } = validate(this.form, RULES)
      this.errors = errors
      if (!valid) return
      this.loading = true
      try {
        await this.registerStudent(this.form)
        this.$router.push('/student/dashboard')
      } catch (err) {
        this.errorMsg = err.response?.data?.message || 'Registration failed.'
      } finally { this.loading = false }
    },
  },
}
</script>
