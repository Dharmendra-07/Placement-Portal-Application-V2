<template>
  <div class="container py-4" style="max-width:680px;">
    <h5 class="fw-bold mb-4">My Profile</h5>

    <div v-if="successMsg"
         class="alert alert-success py-2 small">{{ successMsg }}</div>
    <div v-if="errorMsg"
         class="alert alert-danger py-2 small">{{ errorMsg }}</div>

    <!-- Personal info -->
    <div class="card border-0 shadow-sm mb-3">
      <div class="card-header bg-white fw-semibold">Personal Information</div>
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label small fw-medium">Full Name</label>
            <input v-model="form.full_name" type="text" class="form-control" />
          </div>
          <div class="col-md-6">
            <label class="form-label small fw-medium">Phone</label>
            <input v-model="form.phone" type="tel" class="form-control" />
          </div>
          <div class="col-md-4">
            <label class="form-label small fw-medium">Gender</label>
            <select v-model="form.gender" class="form-select">
              <option value="">Prefer not to say</option>
              <option>Male</option>
              <option>Female</option>
              <option>Other</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label small fw-medium">Date of Birth</label>
            <input v-model="form.dob" type="date" class="form-control" />
          </div>
          <div class="col-md-4">
            <label class="form-label small fw-medium">Roll Number</label>
            <input :value="form.roll_number" type="text"
                   class="form-control" disabled />
          </div>
          <div class="col-12">
            <label class="form-label small fw-medium">Address</label>
            <textarea v-model="form.address" class="form-control"
                      rows="2"></textarea>
          </div>
        </div>
      </div>
    </div>

    <!-- Academic & skills -->
    <div class="card border-0 shadow-sm mb-3">
      <div class="card-header bg-white fw-semibold">Academic & Skills</div>
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label small fw-medium">Department / Branch</label>
            <input v-model="form.department" type="text" class="form-control"
                   placeholder="Computer Science and Engineering" />
          </div>
          <div class="col-md-3">
            <label class="form-label small fw-medium">Year</label>
            <select v-model="form.year" class="form-select">
              <option v-for="y in [1,2,3,4]" :key="y" :value="y">
                Year {{ y }}
              </option>
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label small fw-medium">CGPA</label>
            <input v-model.number="form.cgpa" type="number"
                   class="form-control" step="0.01" min="0" max="10"
                   placeholder="8.5" />
          </div>
          <div class="col-12">
            <label class="form-label small fw-medium">
              Skills
              <span class="text-muted">(comma-separated)</span>
            </label>
            <input v-model="form.skills" type="text" class="form-control"
                   placeholder="Python, React, SQL, Machine Learning" />
            <!-- Skills preview -->
            <div v-if="skillChips.length" class="d-flex flex-wrap gap-1 mt-2">
              <span v-for="sk in skillChips" :key="sk"
                    class="badge bg-light text-secondary border">
                {{ sk }}
              </span>
            </div>
          </div>
          <div class="col-12">
            <label class="form-label small fw-medium">About / Career Objective</label>
            <textarea v-model="form.about" class="form-control" rows="3"
                      placeholder="Brief bio or career objective..."></textarea>
          </div>
        </div>
      </div>
    </div>

    <!-- Resume -->
    <div class="card border-0 shadow-sm mb-3">
      <div class="card-header bg-white fw-semibold">Resume</div>
      <div class="card-body">
        <div v-if="form.resume_url" class="d-flex align-items-center gap-3 mb-3">
          <div class="text-muted small">Current resume:</div>
          <a :href="form.resume_url" target="_blank"
             class="btn btn-sm btn-outline-primary">
            View / Download
          </a>
        </div>
        <div v-else class="text-muted small mb-3">
          No resume uploaded yet.
        </div>
        <label class="form-label small fw-medium">Upload new resume</label>
        <input type="file" class="form-control" accept=".pdf,.doc,.docx"
               @change="resumeFile = $event.target.files[0]" />
        <div class="text-muted" style="font-size:11px;margin-top:4px;">
          Accepted: PDF, DOC, DOCX · Max 5 MB
        </div>
        <button v-if="resumeFile"
                class="btn btn-sm btn-outline-primary mt-2"
                :disabled="uploading" @click="uploadResume">
          <span v-if="uploading"
                class="spinner-border spinner-border-sm me-1"></span>
          Upload Resume
        </button>
      </div>
    </div>

    <button class="btn btn-primary w-100"
            :disabled="saving" @click="saveProfile">
      <span v-if="saving"
            class="spinner-border spinner-border-sm me-1"></span>
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
      form: {},
      saving: false, uploading: false,
      resumeFile: null,
      successMsg: '', errorMsg: '',
    }
  },
  computed: {
    skillChips() {
      if (!this.form.skills) return []
      return this.form.skills.split(',').map(s => s.trim()).filter(Boolean)
    },
  },
  async created() {
    const { data } = await api.get('/student/profile')
    this.form = { ...data }
  },
  methods: {
    async saveProfile() {
      this.saving     = true
      this.successMsg = ''
      this.errorMsg   = ''
      try {
        await api.put('/student/profile', this.form)
        this.successMsg = 'Profile updated successfully!'
        window.scrollTo({ top: 0, behavior: 'smooth' })
      } catch (err) {
        this.errorMsg = err.response?.data?.message || 'Update failed.'
      } finally { this.saving = false }
    },
    async uploadResume() {
      this.uploading  = true
      this.successMsg = ''
      this.errorMsg   = ''
      const fd        = new FormData()
      fd.append('resume', this.resumeFile)
      try {
        const { data } = await api.post('/student/resume', fd, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        this.form.resume_url = data.resume_url
        this.resumeFile      = null
        this.successMsg      = 'Resume uploaded successfully!'
      } catch (err) {
        this.errorMsg = err.response?.data?.message || 'Upload failed.'
      } finally { this.uploading = false }
    },
  },
}
</script>
