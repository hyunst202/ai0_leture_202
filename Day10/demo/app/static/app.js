"use strict";

const $ = (selector) => document.querySelector(selector);
const state = {user: null, page: 1, pages: 1, selected: null, view: "board", csrf: null, revision: 0};

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function notify(message, error = false) {
  const node = $("#notice");
  node.textContent = message;
  node.className = error ? "notice error" : "notice";
  node.hidden = !message;
}
function action(label, handler, className = "secondary") {
  const node = element("button", label, className);
  node.type = "button";
  node.addEventListener("click", () => run(handler));
  return node;
}
async function run(handler) {
  try { await handler(); } catch (error) { notify(error.message || "요청에 실패했습니다.", true); }
}
async function token() {
  const response = await fetch("/api/auth/csrf", {credentials: "same-origin", cache: "no-store"});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "요청 확인 토큰을 가져올 수 없습니다.");
  state.csrf = data.csrf_token;
  return state.csrf;
}
async function api(path, method = "GET", body) {
  const options = {method, credentials: "same-origin", cache: "no-store", headers: {}};
  if (method !== "GET") {
    options.headers["X-CSRFToken"] = state.csrf || await token();
    if (body !== undefined) { options.headers["Content-Type"] = "application/json"; options.body = JSON.stringify(body); }
  }
  const response = await fetch(path, options);
  const data = response.status === 204 ? {} : await response.json();
  if (!response.ok) {
    if (response.status === 401) { state.user = null; header(); }
    throw new Error(data.error || "요청을 처리할 수 없습니다.");
  }
  return data;
}
function date(value, short = false) {
  return new Intl.DateTimeFormat("ko-KR", short ? {month: "2-digit", day: "2-digit"} : {dateStyle: "medium", timeStyle: "short"}).format(new Date(value));
}
function header() {
  $("#current-user").textContent = state.user ? `${state.user.nickname} 님` : "";
  $("#nav-auth").textContent = state.user ? "로그아웃" : "로그인";
  $("#nav-rules").hidden = state.user?.role !== "ADMIN";
}
function clearSelection() {
  state.revision += 1;
  state.selected = null;
  $("#selection").replaceChildren();
  $("#selection").hidden = true;
}
function area(view) {
  state.view = view;
  clearSelection();
  for (const name of ["board", "auth", "rules"]) $(`#${name}-view`).hidden = name !== view;
}
async function board() { area("board"); await posts(); }
async function posts() {
  const data = await api(`/api/posts?page=${state.page}`);
  state.page = data.page; state.pages = data.total_pages;
  $("#post-count").textContent = `${data.total}개`;
  $("#empty-posts").hidden = data.items.length > 0;
  const tbody = $("#post-list"); tbody.replaceChildren();
  for (const item of data.items) {
    const row = element("tr");
    const title = element("td"); title.append(action(item.title, () => detail(item.id), "post-link"));
    row.append(title, element("td", item.author), element("td", date(item.created_at, true)));
    tbody.append(row);
  }
  const pagination = $("#pagination"); pagination.replaceChildren();
  const pageButton = (label, target, disabled = false) => {
    const button = action(label, async () => { clearSelection(); state.page = target; await posts(); });
    button.disabled = disabled;
    if (typeof label === "number") { button.setAttribute("aria-label", `${label}페이지`); if (label === state.page) button.setAttribute("aria-current", "page"); }
    return button;
  };
  pagination.append(pageButton("이전", state.page - 1, state.page === 1));
  const start = Math.max(1, Math.min(state.page - 2, state.pages - 4));
  for (let page = start; page <= Math.min(start + 4, state.pages); page++) pagination.append(pageButton(page, page));
  pagination.append(pageButton("다음", state.page + 1, state.page === state.pages));
}
function inputField(form, label, name, type, limit, value = "", hint = "") {
  const wrapper = element("div", null, "field");
  const input = type === "textarea" ? element("textarea") : element("input");
  input.id = `field-${name}`; input.name = name; input.required = true; input.value = value;
  if (type !== "textarea") input.type = type;
  input.maxLength = limit * 2;
  if (name === "email") input.autocomplete = "email";
  if (name === "nickname") input.autocomplete = "nickname";
  if (type === "password") input.autocomplete = state.authMode === "signup" ? "new-password" : "current-password";
  const caption = element("label", label); caption.htmlFor = input.id;
  wrapper.append(caption, input);
  if (hint) { const note = element("p", hint, "field-hint"); note.id = `${input.id}-hint`; wrapper.append(note); input.setAttribute("aria-describedby", note.id); }
  form.append(wrapper);
  return input;
}
function submitForm(form, label, handler) {
  const submit = element("button", label, "primary"); submit.type = "submit"; form.append(submit);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (submit.disabled) return;
    submit.disabled = true;
    run(async () => { try { await handler(new FormData(form)); } finally { submit.disabled = false; } });
  });
  return submit;
}
function bounded(value, label, max) {
  if (!value.trim() || Array.from(value).length > max) throw new Error(`${label}은(는) 1~${max.toLocaleString()}자로 입력해주세요.`);
  return value;
}
async function detail(id) {
  state.selected = id;
  const revision = ++state.revision;
  const [data, comments] = await Promise.all([api(`/api/posts/${id}`), api(`/api/posts/${id}/comments`)]);
  if (revision !== state.revision || state.view !== "board") return;
  const item = data.item;
  const root = $("#selection"); root.replaceChildren(); root.hidden = false;
  const heading = element("div", null, "selection-heading");
  const title = element("div"); title.append(element("h2", item.title), element("p", `${item.author} · ${date(item.created_at)}${item.updated_at !== item.created_at ? ` · 수정 ${date(item.updated_at)}` : ""}`, "meta"));
  heading.append(title, action("닫기", clearSelection, "quiet small")); root.append(heading);
  if (item.can_edit) {
    const actions = element("div", null, "actions");
    actions.append(action("수정", () => editor(id)), action("삭제", async () => {
      if (!window.confirm("이 글과 댓글을 삭제할까요?")) return;
      await api(`/api/posts/${id}`, "DELETE"); clearSelection(); await posts(); notify("글을 삭제했습니다.");
    }, "danger small")); root.append(actions);
  }
  root.append(element("p", item.body, "post-body"), element("h3", `댓글 ${comments.items.length}`));
  const list = element("div");
  if (!comments.items.length) list.append(element("p", "아직 댓글이 없습니다.", "muted"));
  for (const comment of comments.items) {
    const article = element("article", null, "comment");
    article.append(element("div", `${comment.author} · ${date(comment.created_at)}`, "meta"), element("p", comment.body)); list.append(article);
  }
  root.append(list);
  if (state.user) {
    const form = element("form", null, "comment-form");
    const input = inputField(form, "댓글", "comment", "textarea", 1000, "", "최대 1,000자"); input.rows = 2;
    submitForm(form, "댓글 등록", async (values) => {
      const body = bounded(values.get("comment"), "댓글", 1000);
      await api(`/api/posts/${id}/comments`, "POST", {body}); await detail(id); notify("댓글을 등록했습니다.");
    }); root.append(form);
  } else root.append(action("로그인하고 댓글 남기기", () => auth("login")));
  root.scrollIntoView({behavior: "smooth", block: "start"});
}
async function editor(id = null) {
  if (!state.user) { auth("login"); notify("로그인 후 글을 작성할 수 있습니다."); return; }
  const revision = ++state.revision;
  const item = id ? (await api(`/api/posts/${id}/edit`)).item : {title: "", body: ""};
  if (revision !== state.revision) return;
  state.selected = id;
  const root = $("#selection"); root.replaceChildren(); root.hidden = false;
  root.append(element("h2", id ? "글 수정" : "새 글 쓰기"));
  const form = element("form");
  const title = inputField(form, "제목", "title", "text", 200, item.title, "최대 200자");
  inputField(form, "본문", "body", "textarea", 10000, item.body, "최대 10,000자 · 줄바꿈을 그대로 저장합니다.");
  submitForm(form, "저장", async (values) => {
    const body = {title: bounded(values.get("title"), "제목", 200), body: bounded(values.get("body"), "본문", 10000)};
    const saved = await api(id ? `/api/posts/${id}` : "/api/posts", id ? "PATCH" : "POST", body);
    if (!id) state.page = 1;
    await posts(); await detail(id || saved.id); notify(id ? "글을 수정했습니다." : "글을 등록했습니다.");
  });
  form.append(action("취소", () => id ? detail(id) : clearSelection(), "quiet"));
  root.append(form); title.focus(); root.scrollIntoView({behavior: "smooth", block: "start"});
}
function auth(mode = "login", address = "") {
  area("auth"); state.authMode = mode; notify("");
  const titles = {login: "로그인", signup: "회원가입", forgot: "비밀번호 찾기"};
  const root = $("#auth-view"); root.replaceChildren(); root.append(element("h1", titles[mode]), element("p", mode === "forgot" ? "실제 메일은 발송되지 않는 데모 기능입니다." : "나의 기록을 남기고 이야기를 이어가세요.", "muted"));
  const form = element("form");
  inputField(form, "이메일", "email", "email", 254, address);
  if (mode === "signup") inputField(form, "닉네임", "nickname", "text", 30, "", "최대 30자");
  if (mode !== "forgot") inputField(form, "비밀번호", "password", "password", 128, "", "8~128자");
  const submit = submitForm(form, titles[mode], async (values) => {
    const body = {email: values.get("email")};
    if (mode !== "forgot") { body.password = values.get("password"); if (Array.from(body.password).length < 8 || Array.from(body.password).length > 128) throw new Error("비밀번호는 8~128자로 입력해주세요."); }
    if (mode === "signup") body.nickname = bounded(values.get("nickname"), "닉네임", 30);
    const path = mode === "forgot" ? "forgot-password" : mode;
    const data = await api(`/api/auth/${path}`, "POST", body);
    if (mode === "signup") { auth("login", body.email); notify("가입했습니다. 이제 로그인해주세요."); }
    else if (mode === "forgot") notify(data.message);
    else { state.user = data.user; state.csrf = null; await token(); header(); await board(); notify("로그인했습니다."); }
  }); submit.classList.add("wide"); root.append(form);
  const links = element("div", null, "auth-links");
  for (const [key, label] of Object.entries(titles)) if (key !== mode) links.append(action(label, () => auth(key), "quiet"));
  links.append(action("게시판으로", board, "quiet")); root.append(links);
}
async function rules() {
  if (state.user?.role !== "ADMIN") throw new Error("관리자만 사용할 수 있습니다.");
  area("rules"); await ruleList();
}
async function ruleList() {
  const data = await api("/api/admin/masking-rules");
  const root = $("#rule-list"); root.replaceChildren();
  if (!data.items.length) root.append(element("li", "등록된 규칙이 없습니다.", "empty"));
  for (const rule of data.items) {
    const row = element("li", null, "rule-row"); const content = element("div");
    content.append(element("div", `${rule.keyword} → ${rule.replacement}`, "rule-keyword"));
    if (rule.source_url) {
      const details = element("details"); details.append(element("summary", "출처 정보"));
      const link = element("a", "참고 자료 열기"); link.href = rule.source_url; link.target = "_blank"; link.rel = "noopener noreferrer";
      details.append(link); if (rule.source_checked_at) details.append(element("div", `확인: ${date(rule.source_checked_at)}`)); content.append(details);
    }
    row.append(content, action("삭제", async () => { await api(`/api/admin/masking-rules/${rule.id}`, "DELETE"); await ruleList(); notify("규칙을 삭제했습니다. 기존 글에도 적용됩니다."); }, "danger small")); root.append(row);
  }
}
$("#nav-board").addEventListener("click", () => run(board));
$("#rules-back").addEventListener("click", () => run(board));
$("#nav-rules").addEventListener("click", () => run(rules));
$("#new-post").addEventListener("click", () => run(() => editor()));
$("#nav-auth").addEventListener("click", () => run(async () => {
  if (!state.user) { auth(); return; }
  await api("/api/auth/logout", "POST"); state.user = null; state.csrf = null;
  await token(); header(); await board(); notify("로그아웃했습니다.");
}));
$("#rule-form").addEventListener("submit", (event) => {
  event.preventDefault(); const submit = event.currentTarget.querySelector("button"); if (submit.disabled) return;
  submit.disabled = true;
  run(async () => { try { const keyword = bounded($("#rule-keyword").value, "키워드", 100); await api("/api/admin/masking-rules", "POST", {keyword}); $("#rule-keyword").value = ""; await ruleList(); notify("규칙을 추가했습니다. 기존 글에도 적용됩니다."); } finally { submit.disabled = false; } });
});
run(async () => { await token(); state.user = (await api("/api/auth/me")).user; header(); await posts(); });

