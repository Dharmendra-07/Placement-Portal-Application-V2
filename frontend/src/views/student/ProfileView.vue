<template>
  <div class="container py-4" style="max-width: 640px;">
    <h5 class="fw-bold mb-4">My Profile</h5>

    <div v-if="successMsg" class="alert alert-success py-2 small">{{ successMsg }}</div>
    <div v-if="errorMsg"   class="alert alert-danger  py-2 small">{{ errorMsg }}</div>

    <div class="card border-0 shadow-sm mb-3">
      <div class="card-header bg-white fw-semibold">Personal Information</div>
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">Full Name</label>
            <input v-model="form.full_name" type="text" class="form-control" />
          </div>
          <div class="col-md-6">
            <label class="form-label">Phone</label>
            <input v-model="form.phone" type="tel" class="form-control" />
          </div>
          <div class="col-md-6">
            <label class="form-label">Gender</label>
            <select v-model="form.gender" class="form-select">
              <option value="">Prefer not to say</option>
              <option>Male</option><option>Female</option><option>Other</option>
            </select>
          </div>
          <div class="col-md-6">
            <label class="form-label">Date of Birth</label>
            <input v-model="form.dob" type="date" class="form-control" />
          </div>
          <div class="col-12">
            <label class="form-label">Address</label>
            <textarea v-model="form.address" class="form-control" rows="2"></textarea>
          </div>
        </div>
      </div>
    </div>

    <div class="card border-0 shadow-sm mb-3">
      <div class="card-header bg-white fw-semibold">Academic Details</div>
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-4">
            <label class="form-label">Roll Number</label>
            <input :value="form.roll_number" type="text" class="form-control" disabled />
          </div>
          <div class="col-md-8">
            <label class="form-label">Department</label>
            <input v-model="form.department" type="text" class="form-control" />
          </div>
          <div class="col-md-4">
            <label class="form-label">Year</label>
            <select v-model="form.year" class="form-select">
              <option v-for="y in [1,2,3,4]" :key="y" :value="y">Year {{ y }}</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">CGPA</label>
            <input v-model.number="form.cgpa" type="number" class="form-control"
                   step="0.01" min="0" max="10" />
          </div>
          <div class="col-12">
            <label class="form-label">Skills <span class="text-muted small">(comma-separated)</span></label>
            <input v-model="form.skills" type="text" class="form-control"
                   placeholder="Python, React, SQL..." />
          </div>
          <div class="col-12">
            <label class="form-label">About</label>
            <textarea v-model="form.about" class="form-control" rows="3"
                      placeholder="Brief bio or career objective..."></textarea>
          </div>
        </div>
      </div>
    </div>

    <!-- Resume upload -->
    <div class="card border-0 shadow-sm mb-3">
      <div class="card-header bg-white fw-semibold">Resume</div>
      <div class="card-body">
        <div v-if="form.resume_url" class="mb-2 small">
          Current: <a :href="form.resume_url" target="_blank">View Resume</a>
        </div>
        <input type="file" class="form-control" accept=".pdf,.doc,.docx"
               @change="resumeFile = $event.target.files[0]" />
        <button v-if="resumeFile" class="btn btn-sm btn-outline-primary mt-2"
                @click="uploadResume" :disabled="uploading">
          <span v-if="uploading" class="spinner-border spinner-border-sm me-1"></span>
          Upload Resume
        </button>
      </div>
    </div>

    <button class="btn btn-primary w-100" :disabled="saving" @click="saveProfile">
      <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
      Save Changes
    </button>
  </div>
</template>

<script>
import api from '../../api'

export default {
  name: 'StudentProfileView',
  data() {
    return {
      form: {}, loading: true, saving: false, uploading: false,
      resumeFile: null, successMsg: '', errorMsg: '',
    }
  },
  async created() {
    const { data } = await api.get('/student/profile')
    this.form = { ...data }
  },
  methods: {
    async saveProfile() {
      this.saving = true; this.successMsg = ''; this.errorMsg = ''
      try {
        await api.put('/student/profile', this.form)
        this.successMsg = 'Profile updated successfully!'
      } catch (err) {
        this.errorMsg = err.response?.data?.message || 'Update failed.'
      } finally { this.saving = false }
    },
    async uploadResume() {
      this.uploading = true
      const fd = new FormData()
      fd.append('resume', this.resumeFile)
      try {
        const { data } = await api.post('/student/resume', fd, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        this.form.resume_url = data.resume_url
        this.resumeFile = null
        this.successMsg = 'Resume uploaded!'
      } catch (err) {
        this.errorMsg = err.response?.data?.message || 'Upload failed.'
      } finally { this.uploading = false }
    },
  },
}
</script>
