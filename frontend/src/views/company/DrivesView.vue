<template>
  <div class="container-fluid py-4 px-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h5 class="fw-bold mb-0">Placement Drives</h5>
      <button class="btn btn-primary" @click="showForm = !showForm">
        {{ showForm ? 'Cancel' : '+ Create Drive' }}
      </button>
    </div>

    <!-- ── Create / Edit form ── -->
    <div v-if="showForm" class="card border-0 shadow-sm mb-4">
      <div class="card-header bg-white fw-semibold">
        {{ editingId ? 'Edit Drive' : 'New Placement Drive' }}
      </div>
      <div class="card-body">
        <div v-if="formError" class="alert alert-danger py-2 small">{{ formError }}</div>
        <div class="row g-3">
          <div class="col-md-5">
            <label class="form-label small fw-medium">Job title <span class="text-danger">*</span></label>
            <input v-model="form.job_title" type="text" class="form-control"
                   placeholder="Senior Software Engineer" />
          </div>
          <div class="col-md-3">
            <label class="form-label small fw-medium">Job type</label>
            <select v-model="form.job_type" class="form-select">
              <option>Full-time</option>
              <option>Internship</option>
              <option>Part-time</option>
              <option>Contract</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label small fw-medium">Location</label>
            <input v-model="form.location" type="text" class="form-control"
                   placeholder="Bengaluru / Remote" />
          </div>

          <div class="col-12">
            <label class="form-label small fw-medium">Job description</label>
            <textarea v-model="form.job_description" class="form-control" rows="3"
                      placeholder="Describe the role, responsibilities, and benefits..."></textarea>
          </div>

          <div class="col-md-6">
            <label class="form-label small fw-medium">Skills required
              <span class="text-muted">(comma-separated)</span></label>
            <input v-model="form.skills_required" type="text" class="form-control"
                   placeholder="Python, React, SQL, Docker" />
          </div>
          <div class="col-md-3">
            <label class="form-label small fw-medium">Min salary (LPA)</label>
            <input v-model.number="form.salary_min" type="number"
                   class="form-control" placeholder="6" />
          </div>
          <div class="col-md-3">
            <label class="form-label small fw-medium">Max salary (LPA)</label>
            <input v-model.number="form.salary_max" type="number"
                   class="form-control" placeholder="12" />
          </div>

          <div class="col-md-4">
            <label class="form-label small fw-medium">Eligible branches
              <span class="text-muted">(comma-separated)</span></label>
            <input v-model="form.eligible_branches" type="text" class="form-control"
                   placeholder="CSE, ECE, IT" />
          </div>
          <div class="col-md-4">
            <label class="form-label small fw-medium">Eligible years
              <span class="text-muted">(e.g. 3,4)</span></label>
            <input v-model="form.eligible_years" type="text" class="form-control"
                   placeholder="3, 4" />
          </div>
          <div class="col-md-4">
            <label class="form-label small fw-medium">Min CGPA</label>
            <input v-model.number="form.min_cgpa" type="number" step="0.1"
                   min="0" max="10" class="form-control" placeholder="7.0" />
          </div>

          <div class="col-md-6">
            <label class="form-label small fw-medium">Application deadline</label>
            <input v-model="form.application_deadline"
                   type="datetime-local" class="form-control" />
          </div>
          <div class="col-md-6">
            <label class="form-label small fw-medium">Drive / interview date</label>
            <input v-model="form.drive_date"
                   type="datetime-local" class="form-control" />
          </div>
        </div>

        <div class="d-flex gap-2 mt-3">
          <button class="btn btn-success" :disabled="submitting" @click="submitDrive">
            <span v-if="submitting"
                  class="spinner-border spinner-border-sm me-1"></span>
            {{ editingId ? 'Update Drive' : 'Submit for Approval' }}
          </button>
          <button class="btn btn-outline-secondary" @click="cancelForm">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- ── Filter bar ── -->
    <div class="d-flex gap-2 mb-3 flex-wrap">
      <button v-for="tab in tabs" :key="tab.value"
              class="btn btn-sm"
              :class="activeTab === tab.value
                ? 'btn-primary' : 'btn-outline-secondary'"
              @click="activeTab = tab.value">
        {{ tab.label }}
        <span v-if="counts[tab.value]"
              class="badge ms-1"
              :class="activeTab === tab.value ? 'bg-white text-primary' : 'bg-secondary'">
          {{ counts[tab.value] }}
        </span>
      </button>
    </div>

    <!-- ── Drive cards ── -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else-if="filteredDrives.length === 0"
         class="text-muted text-center py-5">
      No drives in this category.
    </div>
    <div v-else class="row g-3">
      <div class="col-md-6 col-lg-4" v-for="d in filteredDrives" :key="d.id">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <h6 class="fw-bold mb-0">{{ d.job_title }}</h6>
              <span class="badge" :class="statusBadge(d.status)">{{ d.status }}</span>
            </div>
            <p class="text-muted small mb-2">
              {{ d.job_type }} · {{ d.location || 'Remote' }}
            </p>
            <div class="row g-1 small text-muted">
              <div class="col-6">
                Salary: {{ d.salary_min ? `₹${d.salary_min}–${d.salary_max} LPA` : '—' }}
              </div>
              <div class="col-6">Min CGPA: {{ d.min_cgpa }}</div>
              <div class="col-6">Branches: {{ d.eligible_branches || 'All' }}</div>
              <div class="col-6">Deadline: {{ formatDate(d.application_deadline) }}</div>
            </div>
          </div>
          <div class="card-footer bg-transparent d-flex gap-2 flex-wrap">
            <router-link :to="`/company/applicants/${d.id}`"
                         class="btn btn-sm btn-outline-primary flex-fill">
              Applicants
              <span v-if="d.applicant_count"
                    class="badge bg-primary ms-1">{{ d.applicant_count }}</span>
            </router-link>
            <button v-if="d.status !== 'closed'"
                    class="btn btn-sm btn-outline-secondary"
                    @click="startEdit(d)">Edit</button>
            <button v-if="d.status === 'approved'"
                    class="btn btn-sm btn-outline-danger"
                    @click="closeDrive(d.id)">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../api'

const EMPTY_FORM = () => ({
  job_title: '', job_type: 'Full-time', location: '',
  job_description: '', skills_required: '',
  salary_min: '', salary_max: '',
  eligible_branches: '', eligible_years: '', min_cgpa: 0,
  application_deadline: '', drive_date: '',
})

export default {
  name: 'CompanyDrivesView',
  data() {
    return {
      drives: [], loading: true, showForm: false,
      submitting: false, formError: '',
      editingId: null,
      form: EMPTY_FORM(),
      activeTab: 'all',
      tabs: [
        { label: 'All',      value: 'all'      },
        { label: 'Active',   value: 'approved' },
        { label: 'Pending',  value: 'pending'  },
        { label: 'Closed',   value: 'closed'   },
      ],
    }
  },
  computed: {
    filteredDrives() {
      if (this.activeTab === 'all') return this.drives
      return this.drives.filter(d => d.status === this.activeTab)
    },
    counts() {
      return {
        approved: this.drives.filter(d => d.status === 'approved').length,
        pending:  this.drives.filter(d => d.status === 'pending').length,
        closed:   this.drives.filter(d => d.status === 'closed').length,
      }
    },
  },
  created() { this.fetchDrives() },
  methods: {
    async fetchDrives() {
      this.loading = true
      try {
        const { data } = await api.get('/company/drives')
        this.drives = data
      } finally { this.loading = false }
    },
    startEdit(d) {
      this.editingId = d.id
      this.form = {
        job_title: d.job_title, job_type: d.job_type, location: d.location || '',
        job_description: d.job_description || '',
        skills_required: d.skills_required || '',
        salary_min: d.salary_min || '', salary_max: d.salary_max || '',
        eligible_branches: d.eligible_branches || '',
        eligible_years: d.eligible_years || '',
        min_cgpa: d.min_cgpa || 0,
        application_deadline: d.application_deadline
          ? d.application_deadline.slice(0, 16) : '',
        drive_date: d.drive_date ? d.drive_date.slice(0, 16) : '',
      }
      this.showForm = true
      window.scrollTo({ top: 0, behavior: 'smooth' })
    },
    cancelForm() {
      this.showForm  = false
      this.editingId = null
      this.form      = EMPTY_FORM()
      this.formError = ''
    },
    async submitDrive() {
      this.formError = ''
      if (!this.form.job_title.trim()) {
        this.formError = 'Job title is required.'
        return
      }
      this.submitting = true
      try {
        if (this.editingId) {
          await api.put(`/company/drives/${this.editingId}`, this.form)
        } else {
          await api.post('/company/drives', this.form)
        }
        this.cancelForm()
        this.fetchDrives()
      } catch (err) {
        this.formError = err.response?.data?.message || 'Failed to save drive.'
      } finally { this.submitting = false }
    },
    async closeDrive(id) {
      if (!confirm('Close this drive? Students will no longer be able to apply.')) return
      await api.put(`/company/drives/${id}/close`)
      this.fetchDrives()
    },
    statusBadge(s) {
      return {
        pending:  'bg-warning text-dark',
        approved: 'bg-success',
        closed:   'bg-secondary',
      }[s] || 'bg-secondary'
    },
    formatDate(d) {
      return d ? new Date(d).toLocaleDateString('en-IN') : '—'
    },
  },
}
</script>
