const apiBase = "/api/v1";
const form = document.querySelector("#create-project-form");
const projectList = document.querySelector("#project-list");
const projectCount = document.querySelector("#project-count");
const notice = document.querySelector("#notice");
const selectedPanel = document.querySelector("#selected-project");
let projects = [];
let selectedProjectId = null;

function showNotice(message, isSuccess = false) {
	notice.textContent = message;
	notice.classList.toggle("success", isSuccess);
	notice.hidden = false;
}

function hideNotice() {
	notice.hidden = true;
	notice.textContent = "";
}

async function request(path, options = {}) {
	const response = await fetch(`${apiBase}${path}`, {
		...options,
		headers: { "Content-Type": "application/json", ...options.headers },
	});
	if (!response.ok) {
		const body = await response.json().catch(() => ({}));
		throw new Error(body.detail || `Request failed (${response.status})`);
	}
	if (response.status === 204) return null;
	return response.json();
}

function renderSelectedProject(project) {
	selectedPanel.hidden = !project;
	if (!project) {
		selectedPanel.replaceChildren();
		return;
	}

	const title = document.createElement("h2");
	title.textContent = project.name;
	const description = document.createElement("p");
	description.textContent = project.description || "No description added.";
	const documents = document.createElement("div");
	documents.className = "document-placeholder";
	documents.textContent =
		"Document uploads will be available in the next step.";
	selectedPanel.replaceChildren(title, description, documents);
}

function renderProjects() {
	projectCount.textContent = String(projects.length);
	if (!projects.some((project) => project.id === selectedProjectId)) {
		selectedProjectId = projects[0]?.id ?? null;
	}

	if (projects.length === 0) {
		projectList.innerHTML =
			'<p class="empty-state">No projects yet. Create one to get started.</p>';
		renderSelectedProject(null);
		return;
	}

	projectList.replaceChildren();
	for (const project of projects) {
		const row = document.createElement("article");
		row.className = `project-row${project.id === selectedProjectId ? " selected" : ""}`;

		const select = document.createElement("button");
		select.type = "button";
		select.className = "project-select";
		select.setAttribute(
			"aria-pressed",
			String(project.id === selectedProjectId),
		);
		const name = document.createElement("span");
		name.className = "project-name";
		name.textContent = project.name;
		const description = document.createElement("span");
		description.className = "project-description";
		description.textContent =
			project.description || "Select to view this project";
		select.append(name, description);
		select.addEventListener("click", () => {
			selectedProjectId = project.id;
			renderProjects();
		});

		const remove = document.createElement("button");
		remove.type = "button";
		remove.className = "delete-button";
		remove.textContent = "Delete";
		remove.setAttribute("aria-label", `Delete ${project.name}`);
		remove.addEventListener("click", () => deleteProject(project));

		row.append(select, remove);
		projectList.append(row);
	}

	renderSelectedProject(
		projects.find((project) => project.id === selectedProjectId),
	);
}

async function loadProjects() {
	projectList.innerHTML = '<p class="empty-state">Loading projects…</p>';
	try {
		projects = await request("/projects");
		hideNotice();
		renderProjects();
	} catch (error) {
		projectList.innerHTML =
			'<p class="empty-state">Projects could not be loaded.</p>';
		renderSelectedProject(null);
		showNotice(error.message);
	}
}

async function deleteProject(project) {
	if (
		!window.confirm(
			`Delete “${project.name}”? This will also remove its documents.`,
		)
	)
		return;
	try {
		await request(`/projects/${project.id}`, { method: "DELETE" });
		projects = projects.filter((item) => item.id !== project.id);
		hideNotice();
		renderProjects();
		showNotice("Project deleted.", true);
	} catch (error) {
		showNotice(error.message);
	}
}

form.addEventListener("submit", async (event) => {
	event.preventDefault();
	const submitButton = form.querySelector("button[type='submit']");
	submitButton.disabled = true;
	hideNotice();
	const formData = new FormData(form);
	try {
		const project = await request("/projects", {
			method: "POST",
			body: JSON.stringify({
				name: formData.get("name"),
				description: formData.get("description") || null,
			}),
		});
		projects = [project, ...projects];
		selectedProjectId = project.id;
		form.reset();
		renderProjects();
		showNotice("Project created.", true);
	} catch (error) {
		showNotice(error.message);
	} finally {
		submitButton.disabled = false;
	}
});

document
	.querySelector("#refresh-projects")
	.addEventListener("click", loadProjects);
loadProjects();
