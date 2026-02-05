import React, { useEffect, useMemo, useState } from "react";
import PageHeader from "../../ui/components/PageHeader";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";
import SuccessAlert from "../../ui/components/SuccessAlert";
import { useAuth } from "../../ui/auth";
import { theme } from "../../theme";
import {
  Group,
  Permission,
  StandardRole,
  User,
  UserPayload,
  createGroup,
  createUser,
  deleteGroup,
  deleteUser,
  listGroups,
  listPermissions,
  listStandardRoles,
  listUsers,
  resetUserPassword,
  updateGroup,
  updateUser,
} from "../../services/users";

const emptyUser: UserPayload = {
  username: "",
  first_name: "",
  last_name: "",
  email: "",
  is_active: true,
  is_staff: false,
  is_superuser: false,
  groups: [],
  user_permissions: [],
  password: "",
};

type GroupForm = {
  id: number | null;
  name: string;
  permissions: number[];
};

export default function UserSettings() {
  const { token } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [standardRoles, setStandardRoles] = useState<StandardRole[]>([]);

  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [userForm, setUserForm] = useState<UserPayload>(emptyUser);
  const [passwordInput, setPasswordInput] = useState("");
  const [search, setSearch] = useState("");

  const [groupForm, setGroupForm] = useState<GroupForm>({
    id: null,
    name: "",
    permissions: [],
  });

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function loadAll() {
    if (!token) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const [u, g, p, sr] = await Promise.all([
        listUsers(token),
        listGroups(token),
        listPermissions(token),
        listStandardRoles(token),
      ]);
      setUsers(u);
      setGroups(g);
      setPermissions(p);
      setStandardRoles(sr);
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to load user settings.");
    } finally {
      setIsLoading(false);
    }
  }

  async function ensureStandardRole(name: string) {
    if (!token) return;
    const exists = groups.some((g) => g.name === name);
    if (exists) return;
    await createGroup(token, { name, permissions: [] });
    await loadAll();
  }

  const filteredUsers = useMemo(() => {
    if (!search) return users;
    const q = search.toLowerCase();
    return users.filter(
      (u) =>
        u.username.toLowerCase().includes(q) ||
        u.email?.toLowerCase().includes(q) ||
        `${u.first_name} ${u.last_name}`.toLowerCase().includes(q)
    );
  }, [users, search]);

  function selectUser(u: User) {
    setSelectedUserId(u.id);
    setUserForm({
      username: u.username,
      first_name: u.first_name,
      last_name: u.last_name,
      email: u.email,
      is_active: u.is_active,
      is_staff: u.is_staff,
      is_superuser: u.is_superuser,
      groups: u.groups || [],
      user_permissions: u.user_permissions || [],
      password: "",
    });
    setPasswordInput("");
  }

  function startNewUser() {
    setSelectedUserId(null);
    setUserForm(emptyUser);
    setPasswordInput("");
  }

  async function handleSaveUser() {
    if (!token) return;
    setIsSaving(true);
    setErrorMsg(null);
    setStatusMsg(null);
    try {
      const payload = {
        ...userForm,
        password: userForm.password?.trim() ? userForm.password : undefined,
      };
      let saved: User;
      if (selectedUserId) {
        saved = await updateUser(token, selectedUserId, payload);
      } else {
        saved = await createUser(token, payload as UserPayload);
      }
      await loadAll();
      setStatusMsg(`User "${saved.username}" saved.`);
      const refreshed = users.find((u) => u.id === saved.id) || saved;
      selectUser(refreshed as User);
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to save user.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteUser() {
    if (!token || !selectedUserId) return;
    const confirmDelete = window.confirm("Delete this user?");
    if (!confirmDelete) return;
    setIsSaving(true);
    setErrorMsg(null);
    setStatusMsg(null);
    try {
      await deleteUser(token, selectedUserId);
      setStatusMsg("User deleted.");
      startNewUser();
      await loadAll();
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to delete user.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleResetPassword() {
    if (!token || !selectedUserId) return;
    if (!passwordInput.trim()) {
      setErrorMsg("Please enter a new password.");
      return;
    }
    setIsSaving(true);
    setErrorMsg(null);
    setStatusMsg(null);
    try {
      await resetUserPassword(token, selectedUserId, passwordInput.trim());
      setPasswordInput("");
      setStatusMsg("Password reset successfully.");
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to reset password.");
    } finally {
      setIsSaving(false);
    }
  }

  function toggleIdInList(list: number[], id: number) {
    return list.includes(id) ? list.filter((x) => x !== id) : [...list, id];
  }

  const effectivePermissions = useMemo(() => {
    const fromGroups = new Set<number>();
    userForm.groups.forEach((gid) => {
      const g = groups.find((gr) => gr.id === gid);
      g?.permissions?.forEach((pid) => fromGroups.add(pid));
    });
    const direct = new Set(userForm.user_permissions || []);
    const combined = new Set([...Array.from(fromGroups), ...Array.from(direct)]);
    return permissions.filter((p) => combined.has(p.id));
  }, [userForm.groups, userForm.user_permissions, groups, permissions]);

  // Role (group) helpers
  function selectGroup(g: Group) {
    setGroupForm({ id: g.id, name: g.name, permissions: g.permissions || [] });
  }

  function startNewGroup() {
    setGroupForm({ id: null, name: "", permissions: [] });
  }

  async function handleSaveGroup() {
    if (!token) return;
    setIsSaving(true);
    setErrorMsg(null);
    setStatusMsg(null);
    try {
      if (groupForm.id) {
        await updateGroup(token, groupForm.id, {
          name: groupForm.name,
          permissions: groupForm.permissions,
        });
      } else {
        await createGroup(token, {
          name: groupForm.name,
          permissions: groupForm.permissions,
        });
      }
      setStatusMsg("Role saved.");
      await loadAll();
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to save role.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteGroup() {
    if (!token || !groupForm.id) return;
    const confirmDelete = window.confirm("Delete this role?");
    if (!confirmDelete) return;
    setIsSaving(true);
    setErrorMsg(null);
    setStatusMsg(null);
    try {
      await deleteGroup(token, groupForm.id);
      setStatusMsg("Role deleted.");
      startNewGroup();
      await loadAll();
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to delete role.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <PageHeader
        title="User Settings"
        subtitle="Manage users, roles, passwords, and permissions."
        actions={
          <Button variant="secondary" onClick={loadAll} disabled={isLoading}>
            Refresh
          </Button>
        }
      />

      {errorMsg && <ErrorAlert message={errorMsg} onDismiss={() => setErrorMsg(null)} />}
      {statusMsg && <SuccessAlert message={statusMsg} onDismiss={() => setStatusMsg(null)} />}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.6fr 1fr",
          gap: 20,
          alignItems: "start",
        }}
      >
        <div
          style={{
            background: "white",
            border: `1px solid ${theme.colors.border}`,
            borderRadius: theme.radius.lg,
            padding: 16,
            display: "grid",
            gridTemplateColumns: "1fr 1.2fr",
            gap: 12,
            minHeight: 560,
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 8, minHeight: 0 }}>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search users"
                style={{
                  flex: 1,
                  padding: 10,
                  borderRadius: theme.radius.base,
                  border: `1px solid ${theme.colors.border}`,
                }}
              />
              <Button variant="accent" onClick={startNewUser}>
                New
              </Button>
            </div>
            <div
              style={{
                flex: 1,
                minHeight: 0,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.radius.base,
                overflow: "auto",
              }}
            >
              {isLoading ? (
                <div style={{ padding: 12 }}>Loading users...</div>
              ) : filteredUsers.length === 0 ? (
                <div style={{ padding: 12, color: theme.colors.textTertiary }}>No users</div>
              ) : (
                filteredUsers.map((u) => {
                  const isActive = u.is_active;
                  const isSelected = u.id === selectedUserId;
                  return (
                    <div
                      key={u.id}
                      onClick={() => selectUser(u)}
                      style={{
                        padding: "10px 12px",
                        borderBottom: `1px solid ${theme.colors.borderLight}`,
                        cursor: "pointer",
                        backgroundColor: isSelected ? theme.colors.brandBlueSoft : "white",
                      }}
                    >
                      <div style={{ fontWeight: 600, color: theme.colors.textPrimary }}>
                        {u.username} {!isActive && <span style={{ color: theme.colors.danger }}>(inactive)</span>}
                      </div>
                      <div style={{ fontSize: 13, color: theme.colors.textTertiary }}>{u.email || "—"}</div>
                      <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
                        Roles: {u.groups?.length ? u.groups.map((gid) => groups.find((g) => g.id === gid)?.name || gid).join(", ") : "none"}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div>
                <label style={labelStyle}>Username</label>
                <input
                  value={userForm.username}
                  onChange={(e) => setUserForm({ ...userForm, username: e.target.value })}
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={labelStyle}>Email</label>
                <input
                  value={userForm.email}
                  onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={labelStyle}>First name</label>
                <input
                  value={userForm.first_name}
                  onChange={(e) => setUserForm({ ...userForm, first_name: e.target.value })}
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={labelStyle}>Last name</label>
                <input
                  value={userForm.last_name}
                  onChange={(e) => setUserForm({ ...userForm, last_name: e.target.value })}
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={labelStyle}>Password (only to set / change)</label>
                <input
                  type="password"
                  value={userForm.password || ""}
                  onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                  placeholder={selectedUserId ? "Leave blank to keep current" : ""}
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={labelStyle}>Status</label>
                <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
                  <label style={checkboxLabelStyle}>
                    <input
                      type="checkbox"
                      checked={userForm.is_active}
                      onChange={(e) => setUserForm({ ...userForm, is_active: e.target.checked })}
                    />
                    Active
                  </label>
                  <label style={checkboxLabelStyle}>
                    <input
                      type="checkbox"
                      checked={userForm.is_staff}
                      onChange={(e) => setUserForm({ ...userForm, is_staff: e.target.checked })}
                    />
                    Staff
                  </label>
                  <label style={checkboxLabelStyle}>
                    <input
                      type="checkbox"
                      checked={userForm.is_superuser}
                      onChange={(e) => setUserForm({ ...userForm, is_superuser: e.target.checked })}
                    />
                    Superuser
                  </label>
                </div>
              </div>
            </div>

            <div
              style={{
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.radius.base,
                padding: 12,
              }}
            >
              <div style={{ fontWeight: 600, marginBottom: 8 }}>Roles (Groups)</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 8 }}>
                {groups.map((g) => (
                  <label key={g.id} style={checkboxLabelStyle}>
                    <input
                      type="checkbox"
                      checked={userForm.groups.includes(g.id)}
                      onChange={() =>
                        setUserForm({
                          ...userForm,
                          groups: toggleIdInList(userForm.groups, g.id),
                        })
                      }
                    />
                    {g.name}
                  </label>
                ))}
              </div>
            </div>

            <div
              style={{
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.radius.base,
                padding: 12,
              }}
            >
              <div style={{ fontWeight: 600, marginBottom: 8 }}>Direct Permissions</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 6, maxHeight: 220, overflow: "auto" }}>
                {permissions.map((p) => (
                  <label key={p.id} style={checkboxLabelStyle}>
                    <input
                      type="checkbox"
                      checked={userForm.user_permissions.includes(p.id)}
                      onChange={() =>
                        setUserForm({
                          ...userForm,
                          user_permissions: toggleIdInList(userForm.user_permissions, p.id),
                        })
                      }
                    />
                    {p.codename} <span style={{ color: theme.colors.textTertiary }}>({p.app_label || "app"})</span>
                  </label>
                ))}
              </div>
              <div style={{ marginTop: 10, fontSize: 12, color: theme.colors.textTertiary }}>
                Effective permissions include role permissions plus the direct permissions above.
              </div>
            </div>

            <div
              style={{
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.radius.base,
                padding: 12,
              }}
            >
              <div style={{ fontWeight: 600, marginBottom: 6 }}>Effective permissions</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {effectivePermissions.map((p) => (
                  <span
                    key={p.id}
                    style={{
                      background: theme.colors.brandBlueSoft,
                      color: theme.colors.brandBlueDark,
                      padding: "4px 8px",
                      borderRadius: theme.radius.base,
                      fontSize: 12,
                    }}
                  >
                    {p.codename}
                  </span>
                ))}
                {effectivePermissions.length === 0 && (
                  <span style={{ color: theme.colors.textTertiary }}>No permissions</span>
                )}
              </div>
            </div>

            <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
              <Button onClick={handleSaveUser} disabled={isSaving}>
                {selectedUserId ? "Save user" : "Create user"}
              </Button>
              <Button variant="danger" onClick={handleDeleteUser} disabled={!selectedUserId || isSaving}>
                Delete
              </Button>
              <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                <input
                  type="password"
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  placeholder="New password"
                  style={{ ...inputStyle, width: 180 }}
                />
                <Button variant="warning" onClick={handleResetPassword} disabled={!selectedUserId || isSaving}>
                  Reset password
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Roles / permissions panel */}
        <div
          style={{
            background: "white",
            border: `1px solid ${theme.colors.border}`,
            borderRadius: theme.radius.lg,
            padding: 16,
            display: "flex",
            flexDirection: "column",
            gap: 12,
            minHeight: 560,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ margin: 0 }}>Roles & Permissions</h3>
            <Button variant="accent" onClick={startNewGroup}>
              New role
            </Button>
          </div>
          <div
            style={{
              background: theme.colors.backgroundGray,
              border: `1px dashed ${theme.colors.border}`,
              borderRadius: theme.radius.base,
              padding: 10,
              display: "flex",
              flexWrap: "wrap",
              gap: 8,
            }}
          >
            {standardRoles.map((r) => (
              <Button
                key={r.name}
                variant={r.exists ? "secondary" : "accent"}
                onClick={() => ensureStandardRole(r.name)}
                disabled={isSaving}
              >
                {r.exists ? "Exists" : "Create"} {r.name}
              </Button>
            ))}
            {standardRoles.length === 0 && (
              <div style={{ color: theme.colors.textTertiary, fontSize: 13 }}>
                Standard roles info unavailable.
              </div>
            )}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 8, maxHeight: 180, overflow: "auto" }}>
            {groups.map((g) => (
              <div
                key={g.id}
                style={{
                  padding: 10,
                  border: `1px solid ${groupForm.id === g.id ? theme.colors.brandBlue : theme.colors.border}`,
                  borderRadius: theme.radius.base,
                  cursor: "pointer",
                  background: groupForm.id === g.id ? theme.colors.brandBlueSoft : "white",
                }}
                onClick={() => selectGroup(g)}
              >
                <div style={{ fontWeight: 600 }}>{g.name}</div>
                <div style={{ fontSize: 12, color: theme.colors.textTertiary }}>
                  {g.permissions.length} permission(s)
                </div>
              </div>
            ))}
            {groups.length === 0 && <div style={{ color: theme.colors.textTertiary }}>No roles defined.</div>}
          </div>

          <div style={{ borderTop: `1px solid ${theme.colors.border}`, paddingTop: 10 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 10 }}>
              <div>
                <label style={labelStyle}>Role name</label>
                <input
                  value={groupForm.name}
                  onChange={(e) => setGroupForm({ ...groupForm, name: e.target.value })}
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={labelStyle}>Permissions</label>
                <div
                  style={{
                    maxHeight: 260,
                    overflow: "auto",
                    border: `1px solid ${theme.colors.border}`,
                    borderRadius: theme.radius.base,
                    padding: 8,
                  }}
                >
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 6 }}>
                    {permissions.map((p) => (
                      <label key={p.id} style={checkboxLabelStyle}>
                        <input
                          type="checkbox"
                          checked={groupForm.permissions.includes(p.id)}
                          onChange={() =>
                            setGroupForm({
                              ...groupForm,
                              permissions: toggleIdInList(groupForm.permissions, p.id),
                            })
                          }
                        />
                        {p.codename} <span style={{ color: theme.colors.textTertiary }}>({p.app_label || "app"})</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <Button onClick={handleSaveGroup} disabled={isSaving || !groupForm.name.trim()}>
                  {groupForm.id ? "Save role" : "Create role"}
                </Button>
                <Button variant="danger" onClick={handleDeleteGroup} disabled={!groupForm.id || isSaving}>
                  Delete
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 600,
  color: "#555",
  display: "block",
  marginBottom: 4,
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: theme.radius.base,
  border: `1px solid ${theme.colors.border}`,
  fontSize: 14,
};

const checkboxLabelStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  fontSize: 13,
  color: theme.colors.textPrimary,
};
