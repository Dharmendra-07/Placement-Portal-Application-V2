<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">Selected Candidates</h5>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else-if="placements.length === 0"
         class="text-muted text-center py-5">
      No candidates selected yet.
    </div>
    <div v-else class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr>
            <th>#</th>
            <th>Student</th>
            <th>Position</th>
            <th>Salary (LPA)</th>
            <th>Joining date</th>
            <th>Offer letter</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in placements" :key="p.id">
            <td class="text-muted small">{{ p.id }}</td>
            <td class="fw-medium small">{{ p.student_name }}</td>
            <td class="small">{{ p.position }}</td>
            <td class="small">{{ p.salary ? `₹${p.salary}` : '—' }}</td>
            <td class="small">{{ p.joining_date || '—' }}</td>
            <td class="small">
              <a v-if="p.offer_letter_url"
                 :href="p.offer_letter_url"
                 target="_blank"
                 class="text-decoration-none">View</a>
              <span v-else class="text-muted">—</span>
            </td>
            <td>
              <button class="btn btn-sm btn-outline-secondary"
                      @click="openEdit(p)">Edit</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Inline edit panel -->
    <div v-if="editing" class="card border-0 shadow-sm mt-4">
      <div class="card-header bg-white fw-semibold d-flex justify-content-between">
        Update Placement — {{ editing.student_name }}
        <button class="btn-close" @click="editing = null"></button>
      </div>
      <div class="card-body">
        <div v-if="editError" class="alert alert-danger py-2 small mb-3">
          {{ editError }}
        </div>
        <div class="row g-3">
          <div class="col-md-4">
            <label class="form-label small fw-medium">Position</label>
            <input v-model="editForm.position" type="text" class="form-control" />
          </div>
          <div class="col-md-4">
            <label class="form-label small fw-medium">Salary (LPA)</label>
            <input v-model.number="editForm.salary" type="number"
                   class="form-control" />
          </div>
          <div class="col-md-4">
            <label class="form-label small fw-medium">Joining date</label>
            <input v-model="editForm.joining_date" type="date" class="form-control" />
          </div>
          <div class="col-12">
            <label class="form-label small fw-medium">Offer letter URL</label>
            <input v-model="editForm.offer_letter_url" type="url"
                   class="form-control"
                   placeholder="https://..." />
          </div>
        </div>
        <button class="btn btn-primary mt-3"
                :disabled="saving" @click="savePlacement">
          <span v-if="saving"
                class="spinner-border spinner-border-sm me-1"></span>
          Save
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../api'

export default {
  name: 'CompanyPlacementsView',
  data() {
    return {
      placements: [], loading: true,
      editing: null, editForm: {}, editError: '', saving: false,
    }
  },
  async created() {
    try {
      const { data } = await api.get('/company/placements')
      this.placements = data
    } finally { this.loading = false }
  },
  methods: {
    openEdit(p) {
      this.editing   = p
      this.editForm  = {
        position:         p.position || '',
        salary:           p.salary || '',
        joining_date:     p.joining_date || '',
        offer_letter_url: p.offer_letter_url || '',
      }
      this.editError = ''
    },
    async savePlacement() {
      this.saving = true
      try {
        await api.put(`/company/placements/${this.editing.id}`, this.editForm)
        const { data } = await api.get('/company/placements')
        this.placements = data
        this.editing = null
      } catch (err) {
        this.editError = err.response?.data?.message || 'Save failed.'
      } finally { this.saving = false }
    },
  },
}
</script>
