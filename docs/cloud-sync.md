# 云同步（可选）：登录 + 跨设备

greenroom **默认本地优先**：不登录也能用，工作台存在你这台浏览器里（`localStorage`），刷新还在。
接一个 **免费 [Supabase](https://supabase.com)** 项目即可开启**账号登录 + 跨设备同步**——换电脑/换浏览器登录同一账号，工作台自动拉回来。

设计同 [telos 的做法](https://github.com/YunyueLi/telos)：两张 `jsonb` 表 + 行级安全（RLS），只有本人能读写；**全程只需你操作，约 5 分钟，我们不替你创建账号、不保存任何密钥**。未配置时一切照常本地运行。

数据契约见 [workspace-spec.md](workspace-spec.md)：工作台逻辑模型 = `profile`（账号级：候选人档案 + 简历 + 经历库）+ 一岗一块的 `jobs`。云端就把它们各存一行 `jsonb`。

---

## 1. 新建项目

在 [supabase.com](https://supabase.com) 新建一个免费项目（记住数据库区域即可）。

## 2. 建同步表（SQL Editor 执行）

两张表都受 RLS 保护、仅本人可读写：① `gr_profile` 每人一行（候选人档案 + 简历 + 经历库 + 资料）；② `gr_jobs` 一岗一行（整个岗位的 JD/情报/逐字稿/各轮记录塞进一个 `jsonb`）。语句幂等，可安全重复执行：

```sql
-- 账号级内容：候选人档案 + 简历 + 经历库 + 资料
create table if not exists public.gr_profile (
  user_id    uuid        primary key default auth.uid(),
  data       jsonb       not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);
alter table public.gr_profile enable row level security;
drop policy if exists "own profile" on public.gr_profile;
create policy "own profile" on public.gr_profile
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- 一岗一行：整个岗位塞进一个 jsonb
create table if not exists public.gr_jobs (
  user_id    uuid        not null default auth.uid(),
  slug       text        not null,
  data       jsonb       not null,
  updated_at timestamptz not null default now(),
  primary key (user_id, slug)
);
alter table public.gr_jobs enable row level security;
drop policy if exists "own jobs" on public.gr_jobs;
create policy "own jobs" on public.gr_jobs
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
```

## 3. 配置登录方式（Authentication → Providers）

最省事：保持默认开启的 **Email**（同时支持邮箱+密码）。greenroom MVP 用「邮箱 + 密码」登录/注册。
> 注册若开了邮件确认，注册后需先去邮箱点确认链接才能登录；嫌麻烦可在 Supabase 的 Email 设置里关掉确认（仅自用时）。

## 4. 拿到 URL 和 anon key

**Project Settings → API**：复制 `Project URL` 和 `anon` `public` key。

## 5. 在 greenroom 里填入

打开控制台 → 顶栏齿轮（设置）→ 展开「云同步（可选）」→ 填 `Supabase URL` 和 `anon key` → 保存。
然后用邮箱 + 密码 **注册 / 登录**。登录后：本机工作台先与云端合并、再上传；其它设备登录同账号即自动拉取。

## 6. 防止免费项目闲置暂停（可选）

如果你把 Greenroom 当 hosted 项目使用，Supabase 免费项目长时间没有活动时会发暂停提醒。自部署时可以用 GitHub Actions、Cloudflare Cron、UptimeRobot 或任何定时器每隔数小时触发一次很小的请求。

默认保活可以读取 `gr_profile`，不写用户数据，也不需要 `service_role` key。更稳的做法是在 Supabase SQL Editor 执行一次 [`docs/supabase-keepalive.sql`](supabase-keepalive.sql)，创建一个只会更新单行时间戳的 `gr_touch_keepalive()` RPC；你的定时任务优先调用这个 RPC，失败时再退回只读检查。

如果用 GitHub Actions，自行添加两个 **Actions secrets**：

- `GREENROOM_SUPABASE_URL`：你的 `Project URL`，例如 `https://xxxx.supabase.co`
- `GREENROOM_SUPABASE_ANON_KEY`：Project Settings → API 里的 `anon` `public` key

保存后让 workflow 按计划请求 `POST /rest/v1/rpc/gr_touch_keepalive`，并附带 `apikey` 与 `Authorization: Bearer <anon key>` 请求头。

---

## 合并策略

- **jobs**：按 `slug` 合并；同一岗位两端都改了，`meta.updated` 新的胜（两台设备改不同岗位都不丢）。
- **profile**：子槽位（档案 / 简历 / 经历库）并集，本地优先。
- **library**：按文件路径并集。

冲突极少（同一人很少同时在两台设备改同一个岗位）；MVP 不做复杂冲突界面，沿用「新者胜 + 并集不丢」。

## 安全

- `anon` key 是**公开可暴露**的（受 RLS 保护），可以填进前端 / 设置里。
- **切勿**把 `service_role` key 填进任何前端。
- 真实邮箱/密码只交给 Supabase Auth（加盐哈希、绝不存明文）；greenroom 只在本机 `localStorage` 存登录后的会话令牌。
- 敏感原件（面试录音、大 PDF）按产品形态约定**不进网页云端**，建议只保留在本机文件夹里。
