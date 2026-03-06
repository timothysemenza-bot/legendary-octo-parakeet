function enforceTenantScope(context, resource) {
  if (!context || !resource) {
    return { allowed: false, reason: "Missing context or resource" };
  }

  if (context.client_id !== resource.client_id) {
    return { allowed: false, reason: "Client scope mismatch" };
  }

  if (context.workspace_id !== resource.workspace_id) {
    return { allowed: false, reason: "Workspace scope mismatch" };
  }

  return { allowed: true, reason: "Tenant scope validated" };
}

module.exports = {
  enforceTenantScope
};
