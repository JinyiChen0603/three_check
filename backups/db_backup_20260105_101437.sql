--
-- PostgreSQL database dump
--

\restrict wEBYH7dksULysN1lP1lHPguUXV84rvV9SPcBTPp0pTVRxPmH0cSQZfcECw4Do8I

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: adminreviewstatus; Type: TYPE; Schema: public; Owner: mathtasks
--

CREATE TYPE public.adminreviewstatus AS ENUM (
    'pending',
    'approved',
    'rejected'
);


ALTER TYPE public.adminreviewstatus OWNER TO mathtasks;

--
-- Name: humanreviewstatus; Type: TYPE; Schema: public; Owner: mathtasks
--

CREATE TYPE public.humanreviewstatus AS ENUM (
    'pending',
    'approved',
    'rejected',
    'need_modification'
);


ALTER TYPE public.humanreviewstatus OWNER TO mathtasks;

--
-- Name: materialcategory; Type: TYPE; Schema: public; Owner: mathtasks
--

CREATE TYPE public.materialcategory AS ENUM (
    'high_school_comprehensive',
    'college_comprehensive',
    'high_school_algebra',
    'high_school_geometry',
    'high_school_number_theory',
    'high_school_combinatorics',
    'college_algebra',
    'college_number_theory',
    'college_analysis',
    'college_combinatorics',
    'college_geometry',
    'college_optimization'
);


ALTER TYPE public.materialcategory OWNER TO mathtasks;

--
-- Name: problemsourcetype; Type: TYPE; Schema: public; Owner: mathtasks
--

CREATE TYPE public.problemsourcetype AS ENUM (
    'ocr',
    'manual',
    'ai_variant'
);


ALTER TYPE public.problemsourcetype OWNER TO mathtasks;

--
-- Name: problemstatus; Type: TYPE; Schema: public; Owner: mathtasks
--

CREATE TYPE public.problemstatus AS ENUM (
    'draft',
    'pending_review',
    'published',
    'archived'
);


ALTER TYPE public.problemstatus OWNER TO mathtasks;

--
-- Name: problemvalidationstatus; Type: TYPE; Schema: public; Owner: mathtasks
--

CREATE TYPE public.problemvalidationstatus AS ENUM (
    'not_validated',
    'validating',
    'passed',
    'failed'
);


ALTER TYPE public.problemvalidationstatus OWNER TO mathtasks;

--
-- Name: reviewstatus; Type: TYPE; Schema: public; Owner: mathtasks
--

CREATE TYPE public.reviewstatus AS ENUM (
    'pending',
    'approved',
    'rejected'
);


ALTER TYPE public.reviewstatus OWNER TO mathtasks;

--
-- Name: taskstatus; Type: TYPE; Schema: public; Owner: mathtasks
--

CREATE TYPE public.taskstatus AS ENUM (
    'pending',
    'in_progress',
    'submitted',
    'approved',
    'rejected',
    'timeout'
);


ALTER TYPE public.taskstatus OWNER TO mathtasks;

--
-- Name: tasktype; Type: TYPE; Schema: public; Owner: mathtasks
--

CREATE TYPE public.tasktype AS ENUM (
    'review_problem',
    'create_problem'
);


ALTER TYPE public.tasktype OWNER TO mathtasks;

--
-- Name: transactionstatus; Type: TYPE; Schema: public; Owner: mathtasks
--

CREATE TYPE public.transactionstatus AS ENUM (
    'pending',
    'confirmed',
    'cancelled'
);


ALTER TYPE public.transactionstatus OWNER TO mathtasks;

--
-- Name: transactiontype; Type: TYPE; Schema: public; Owner: mathtasks
--

CREATE TYPE public.transactiontype AS ENUM (
    'problem_reward',
    'review_reward',
    'withdrawal',
    'adjustment'
);


ALTER TYPE public.transactiontype OWNER TO mathtasks;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: mathtasks
--

CREATE TYPE public.userrole AS ENUM (
    'admin',
    'user'
);


ALTER TYPE public.userrole OWNER TO mathtasks;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: material_library; Type: TABLE; Schema: public; Owner: mathtasks
--

CREATE TABLE public.material_library (
    id integer NOT NULL,
    category public.materialcategory NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    baidu_link character varying(500) NOT NULL,
    extract_code character varying(20),
    download_count integer NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.material_library OWNER TO mathtasks;

--
-- Name: material_library_id_seq; Type: SEQUENCE; Schema: public; Owner: mathtasks
--

CREATE SEQUENCE public.material_library_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.material_library_id_seq OWNER TO mathtasks;

--
-- Name: material_library_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mathtasks
--

ALTER SEQUENCE public.material_library_id_seq OWNED BY public.material_library.id;


--
-- Name: problems; Type: TABLE; Schema: public; Owner: mathtasks
--

CREATE TABLE public.problems (
    id integer NOT NULL,
    creator_id integer NOT NULL,
    parent_problem_id integer,
    mongo_id character varying(24),
    title character varying(200) NOT NULL,
    content json,
    explanation text,
    answer text,
    difficulty integer,
    category public.materialcategory,
    source_type public.problemsourcetype NOT NULL,
    ocr_image_url character varying(500),
    version integer NOT NULL,
    variant_count integer NOT NULL,
    validation_status public.problemvalidationstatus NOT NULL,
    validation_result json,
    validation_correct_count integer,
    validation_completed_at timestamp without time zone,
    status public.problemstatus NOT NULL,
    quality_check json,
    quality_check_details json,
    human_review_status public.humanreviewstatus NOT NULL,
    human_review_note text,
    review_count integer NOT NULL,
    avg_innovation_score double precision,
    avg_rigor_score double precision,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    published_at timestamp without time zone
);


ALTER TABLE public.problems OWNER TO mathtasks;

--
-- Name: problems_id_seq; Type: SEQUENCE; Schema: public; Owner: mathtasks
--

CREATE SEQUENCE public.problems_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.problems_id_seq OWNER TO mathtasks;

--
-- Name: problems_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mathtasks
--

ALTER SEQUENCE public.problems_id_seq OWNED BY public.problems.id;


--
-- Name: reviews; Type: TABLE; Schema: public; Owner: mathtasks
--

CREATE TABLE public.reviews (
    id integer NOT NULL,
    problem_id integer,
    validated_problem_id integer,
    reviewer_id integer NOT NULL,
    task_id integer,
    correctness_verification json,
    is_answer_correct boolean,
    innovation_score integer,
    rigor_score integer,
    comment text,
    is_vetoed boolean NOT NULL,
    veto_reason text,
    status public.reviewstatus NOT NULL,
    admin_note text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    approved_at timestamp without time zone
);


ALTER TABLE public.reviews OWNER TO mathtasks;

--
-- Name: reviews_id_seq; Type: SEQUENCE; Schema: public; Owner: mathtasks
--

CREATE SEQUENCE public.reviews_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reviews_id_seq OWNER TO mathtasks;

--
-- Name: reviews_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mathtasks
--

ALTER SEQUENCE public.reviews_id_seq OWNED BY public.reviews.id;


--
-- Name: tasks; Type: TABLE; Schema: public; Owner: mathtasks
--

CREATE TABLE public.tasks (
    id integer NOT NULL,
    problem_id integer,
    validated_problem_id integer,
    user_id integer NOT NULL,
    task_type public.tasktype NOT NULL,
    batch_id character varying(50),
    total_count integer NOT NULL,
    completed_count integer NOT NULL,
    abandoned_count integer NOT NULL,
    status public.taskstatus NOT NULL,
    claimed_at timestamp without time zone,
    expires_at timestamp without time zone,
    submitted_at timestamp without time zone,
    approved_at timestamp without time zone,
    result_data json,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.tasks OWNER TO mathtasks;

--
-- Name: tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: mathtasks
--

CREATE SEQUENCE public.tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tasks_id_seq OWNER TO mathtasks;

--
-- Name: tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mathtasks
--

ALTER SEQUENCE public.tasks_id_seq OWNED BY public.tasks.id;


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: mathtasks
--

CREATE TABLE public.transactions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    amount double precision NOT NULL,
    transaction_type public.transactiontype NOT NULL,
    related_problem_id integer,
    related_task_id integer,
    status public.transactionstatus NOT NULL,
    description character varying(500),
    balance_after double precision,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    confirmed_at timestamp without time zone
);


ALTER TABLE public.transactions OWNER TO mathtasks;

--
-- Name: transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: mathtasks
--

CREATE SEQUENCE public.transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transactions_id_seq OWNER TO mathtasks;

--
-- Name: transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mathtasks
--

ALTER SEQUENCE public.transactions_id_seq OWNED BY public.transactions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: mathtasks
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100),
    password_hash character varying(255) NOT NULL,
    role public.userrole NOT NULL,
    balance double precision NOT NULL,
    problems_created_count integer NOT NULL,
    reviews_completed_count integer NOT NULL,
    is_active boolean NOT NULL,
    is_impersonating boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    last_login_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO mathtasks;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: mathtasks
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO mathtasks;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mathtasks
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: validated_problem_exports; Type: TABLE; Schema: public; Owner: mathtasks
--

CREATE TABLE public.validated_problem_exports (
    id integer NOT NULL,
    user_id integer NOT NULL,
    task_id integer,
    content text NOT NULL,
    answer text NOT NULL,
    explanation text NOT NULL,
    difficulty_validation json,
    originality_check json NOT NULL,
    rigor_check json NOT NULL,
    review_count integer NOT NULL,
    avg_innovation_score double precision,
    avg_rigor_score double precision,
    admin_review_status public.adminreviewstatus NOT NULL,
    admin_reviewer_id integer,
    admin_review_note text,
    admin_reviewed_at timestamp without time zone,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.validated_problem_exports OWNER TO mathtasks;

--
-- Name: validated_problem_exports_id_seq; Type: SEQUENCE; Schema: public; Owner: mathtasks
--

CREATE SEQUENCE public.validated_problem_exports_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.validated_problem_exports_id_seq OWNER TO mathtasks;

--
-- Name: validated_problem_exports_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mathtasks
--

ALTER SEQUENCE public.validated_problem_exports_id_seq OWNED BY public.validated_problem_exports.id;


--
-- Name: validation_records; Type: TABLE; Schema: public; Owner: mathtasks
--

CREATE TABLE public.validation_records (
    id integer NOT NULL,
    validated_problem_id integer,
    validation_type character varying(50) NOT NULL,
    ai_model character varying(100) NOT NULL,
    attempts integer,
    correct_count integer,
    is_passed boolean NOT NULL,
    result_data json NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.validation_records OWNER TO mathtasks;

--
-- Name: validation_records_id_seq; Type: SEQUENCE; Schema: public; Owner: mathtasks
--

CREATE SEQUENCE public.validation_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.validation_records_id_seq OWNER TO mathtasks;

--
-- Name: validation_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mathtasks
--

ALTER SEQUENCE public.validation_records_id_seq OWNED BY public.validation_records.id;


--
-- Name: material_library id; Type: DEFAULT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.material_library ALTER COLUMN id SET DEFAULT nextval('public.material_library_id_seq'::regclass);


--
-- Name: problems id; Type: DEFAULT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.problems ALTER COLUMN id SET DEFAULT nextval('public.problems_id_seq'::regclass);


--
-- Name: reviews id; Type: DEFAULT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.reviews ALTER COLUMN id SET DEFAULT nextval('public.reviews_id_seq'::regclass);


--
-- Name: tasks id; Type: DEFAULT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.tasks ALTER COLUMN id SET DEFAULT nextval('public.tasks_id_seq'::regclass);


--
-- Name: transactions id; Type: DEFAULT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.transactions ALTER COLUMN id SET DEFAULT nextval('public.transactions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: validated_problem_exports id; Type: DEFAULT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.validated_problem_exports ALTER COLUMN id SET DEFAULT nextval('public.validated_problem_exports_id_seq'::regclass);


--
-- Name: validation_records id; Type: DEFAULT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.validation_records ALTER COLUMN id SET DEFAULT nextval('public.validation_records_id_seq'::regclass);


--
-- Data for Name: material_library; Type: TABLE DATA; Schema: public; Owner: mathtasks
--

COPY public.material_library (id, category, title, description, baidu_link, extract_code, download_count, is_active, created_at, updated_at) FROM stdin;
1	high_school_comprehensive	高中数学联赛综合资料包	包含历年高中数学联赛真题及详解，涵盖代数、几何、数论、组合等各个模块	https://pan.baidu.com/s/example_high_school_comp	hs01	0	t	2026-01-04 10:46:38.394576	2026-01-04 10:46:38.394579
2	college_comprehensive	大学数学竞赛综合资料包	包含全国大学生数学竞赛历年真题及详解，涵盖所有模块	https://pan.baidu.com/s/example_college_comp	cl01	0	t	2026-01-04 10:46:38.39458	2026-01-04 10:46:38.39458
3	high_school_algebra	高中数学联赛 - 代数专题	包括函数、方程、不等式、数列等代数问题的系统训练资料	https://pan.baidu.com/s/example_hs_algebra	alg1	0	t	2026-01-04 10:46:38.394583	2026-01-04 10:46:38.394583
4	high_school_geometry	高中数学联赛 - 几何专题	平面几何、解析几何、立体几何等几何问题专项训练	https://pan.baidu.com/s/example_hs_geometry	geo1	0	t	2026-01-04 10:46:38.394584	2026-01-04 10:46:38.394584
5	high_school_number_theory	高中数学联赛 - 数论专题	整除、同余、不定方程等数论问题的系统训练	https://pan.baidu.com/s/example_hs_number	num1	0	t	2026-01-04 10:46:38.394585	2026-01-04 10:46:38.394585
6	high_school_combinatorics	高中数学联赛 - 组合专题	排列组合、图论、组合计数等组合问题专项训练	https://pan.baidu.com/s/example_hs_combo	cmb1	0	t	2026-01-04 10:46:38.394586	2026-01-04 10:46:38.394586
7	college_algebra	大学数学竞赛 - 代数专题	线性代数、抽象代数、群论等高等代数问题训练	https://pan.baidu.com/s/example_cl_algebra	alg2	0	t	2026-01-04 10:46:38.394586	2026-01-04 10:46:38.394587
8	college_number_theory	大学数学竞赛 - 数论专题	初等数论、解析数论等大学数论问题系统训练	https://pan.baidu.com/s/example_cl_number	num2	0	t	2026-01-04 10:46:38.394587	2026-01-04 10:46:38.394588
9	college_analysis	大学数学竞赛 - 分析和方程	数学分析、实分析、复分析、微分方程等问题专项训练	https://pan.baidu.com/s/example_cl_analysis	ana2	0	t	2026-01-04 10:46:38.394588	2026-01-04 10:46:38.394588
10	college_combinatorics	大学数学竞赛 - 组合和概率	组合数学、图论、概率论、随机过程等问题系统训练	https://pan.baidu.com/s/example_cl_combo	cmb2	0	t	2026-01-04 10:46:38.394589	2026-01-04 10:46:38.394589
11	college_geometry	大学数学竞赛 - 几何和拓扑	微分几何、拓扑学、代数拓扑等高等几何问题训练	https://pan.baidu.com/s/example_cl_geometry	geo2	0	t	2026-01-04 10:46:38.394589	2026-01-04 10:46:38.39459
12	college_optimization	大学数学竞赛 - 最优化方法	线性规划、非线性优化、凸优化等最优化问题系统训练	https://pan.baidu.com/s/example_cl_optimization	opt2	0	t	2026-01-04 10:46:38.39459	2026-01-04 10:46:38.39459
\.


--
-- Data for Name: problems; Type: TABLE DATA; Schema: public; Owner: mathtasks
--

COPY public.problems (id, creator_id, parent_problem_id, mongo_id, title, content, explanation, answer, difficulty, category, source_type, ocr_image_url, version, variant_count, validation_status, validation_result, validation_correct_count, validation_completed_at, status, quality_check, quality_check_details, human_review_status, human_review_note, review_count, avg_innovation_score, avg_rigor_score, created_at, updated_at, published_at) FROM stdin;
\.


--
-- Data for Name: reviews; Type: TABLE DATA; Schema: public; Owner: mathtasks
--

COPY public.reviews (id, problem_id, validated_problem_id, reviewer_id, task_id, correctness_verification, is_answer_correct, innovation_score, rigor_score, comment, is_vetoed, veto_reason, status, admin_note, created_at, updated_at, approved_at) FROM stdin;
\.


--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: mathtasks
--

COPY public.tasks (id, problem_id, validated_problem_id, user_id, task_type, batch_id, total_count, completed_count, abandoned_count, status, claimed_at, expires_at, submitted_at, approved_at, result_data, created_at, updated_at) FROM stdin;
1	\N	\N	1	create_problem	imported_01_第一批100题_20260104_104656	8	8	0	submitted	2026-01-04 10:46:56.753687	2027-01-04 10:46:56.753687	2026-01-04 10:46:56.753687	\N	\N	2026-01-04 10:46:56.755647	2026-01-04 10:46:56.755648
2	\N	\N	4	review_problem	batch_69fdc926	8	0	1	rejected	2026-01-04 10:47:54.666034	2026-01-04 22:47:54.666034	\N	\N	\N	2026-01-04 10:47:54.673012	2026-01-04 10:49:24.291329
3	\N	\N	4	review_problem	batch_a41639d1	8	0	1	rejected	2026-01-04 10:49:30.822706	2026-01-04 22:49:30.822706	\N	\N	\N	2026-01-04 10:49:30.825045	2026-01-04 10:53:36.471596
4	\N	\N	4	review_problem	batch_4e5a3aac	8	0	1	rejected	2026-01-04 10:53:40.830741	2026-01-04 22:53:40.830741	\N	\N	\N	2026-01-04 10:53:40.840075	2026-01-04 10:55:29.192443
5	\N	\N	4	review_problem	batch_90b6a0f7	8	0	1	rejected	2026-01-04 10:55:32.971416	2026-01-04 22:55:32.971416	\N	\N	\N	2026-01-04 10:55:32.97451	2026-01-04 10:55:36.087765
6	\N	\N	4	review_problem	batch_a0648f2b	8	0	1	rejected	2026-01-04 10:56:20.330193	2036-01-02 10:56:20.330193	\N	\N	\N	2026-01-04 10:56:20.334997	2026-01-04 10:56:23.334243
\.


--
-- Data for Name: transactions; Type: TABLE DATA; Schema: public; Owner: mathtasks
--

COPY public.transactions (id, user_id, amount, transaction_type, related_problem_id, related_task_id, status, description, balance_after, created_at, updated_at, confirmed_at) FROM stdin;
1	4	10	review_reward	\N	2	confirmed	评分题目 #8	10	2026-01-04 10:48:56.243739	2026-01-04 10:48:56.243741	2026-01-04 10:48:56.239327
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: mathtasks
--

COPY public.users (id, username, email, password_hash, role, balance, problems_created_count, reviews_completed_count, is_active, is_impersonating, created_at, updated_at, last_login_at) FROM stdin;
1	lifanghe	lifanghe@mathtasks.com	$2b$12$q8fKCVri8r2TXJbH.W4jL.aCSMG6yQRgdlBfff1jrxI1xHj6aBjEW	admin	0	0	0	t	f	2026-01-04 10:46:47.294296	2026-01-04 10:46:47.294299	\N
2	gexinlin	gexinlin@mathtasks.com	$2b$12$JbkHQeSswP/EyBhcfMti5u40pZzlBWTgvJfcpva0olrOLEdl0ekuK	admin	0	0	0	t	f	2026-01-04 10:46:47.294301	2026-01-04 10:46:47.294301	\N
3	hewenze	hewenze@mathtasks.com	$2b$12$NHooLRThFkng4m/y5mlaoOKKa5nGMxIMfzUCu4CH5dDwjOjiaRsqi	user	0	0	0	t	f	2026-01-04 10:46:47.294302	2026-01-04 10:46:47.294302	\N
5	zhuzhijun	zhuzhijun@mathtasks.com	$2b$12$.QqXjKEQMZi9T8TjTDpsf.zu9ElKDWJ5dRnqwY9Q9775UK.uD9uAm	user	0	0	0	t	f	2026-01-04 10:46:47.294303	2026-01-04 10:46:47.294303	\N
6	zhaozhuoying	zhaozhuoying@mathtasks.com	$2b$12$L.6b210YmKZr/byuZFLzgOHwpyhwzcDABTlXUzvCdjV3RF25RC0/6	user	0	0	0	t	f	2026-01-04 10:46:47.294304	2026-01-04 10:46:47.294304	\N
7	zhuyoupeng	zhuyoupeng@mathtasks.com	$2b$12$YisK0RBTsofwYb/cEf0wyOVyUBRu3gYLo17La1JA5w379IomplaBi	user	0	0	0	t	f	2026-01-04 10:46:47.294304	2026-01-04 10:46:47.294304	\N
8	mayuzhong	mayuzhong@mathtasks.com	$2b$12$bZHsuXQjMYecqNxMcIvNzOjJ5bTMBgGpil0rBXv3oFwqzDk29QOzq	user	0	0	0	t	f	2026-01-04 10:46:47.294305	2026-01-04 10:46:47.294305	\N
9	kongyusu	kongyusu@mathtasks.com	$2b$12$mf3Ayly.GSPX/ieQMo9b0.Aq4.2IELNa6J/nuL3eYvTGS6FTONXhC	user	0	0	0	t	f	2026-01-04 10:46:47.294305	2026-01-04 10:46:47.294305	\N
10	gaokunyi	gaokunyi@mathtasks.com	$2b$12$hl3gq82whg3OEnu4Wb6D3OiNQgFY5McU.GWalc3t8H3.Vp8rymT7C	user	0	0	0	t	f	2026-01-04 10:46:47.294306	2026-01-04 10:46:47.294306	\N
11	zhujinhong	zhujinhong@mathtasks.com	$2b$12$wVC6Nvkc6et/gvSmASP32egB.1ZGFdqgCB0Xld17r9NeLm5AnS1da	user	0	0	0	t	f	2026-01-04 10:46:47.294306	2026-01-04 10:46:47.294306	\N
12	xieshuhong	xieshuhong@mathtasks.com	$2b$12$3C6tlV70UssV9PavQS5LXeXOUaYKegd1NzK8P6gJhG557aHEs86p2	user	0	0	0	t	f	2026-01-04 10:46:47.294307	2026-01-04 10:46:47.294307	\N
13	sunjungxuan	sunjungxuan@mathtasks.com	$2b$12$e42xjimhkoWEt/Z6Dybm6.AnYmz6kXXImKq.HYP3HM41e3bUXWdfW	user	0	0	0	t	f	2026-01-04 10:46:47.294307	2026-01-04 10:46:47.294308	\N
14	lifanghe123	lifanghe123@mathtasks.com	$2b$12$KND2lKsAOUgy8f.mPvOiV.K/yq4HWfOzbEeQW6BNrVcyyZY3vUHAW	user	0	0	0	t	f	2026-01-04 10:46:47.294308	2026-01-04 10:46:47.294308	\N
15	gexinlin123	gexinlin123@mathtasks.com	$2b$12$Kpfnq2N7G/tUtuWkqNFrFezHPb8ktCdqsEgluasj6Gg4s4nTcsQNy	user	0	0	0	t	f	2026-01-04 10:46:47.294308	2026-01-04 10:46:47.294309	\N
16	penghaihang	penghaihang@mathtasks.com	$2b$12$jPXiqpvl3F5fmBPBG6gtk.kllNJrqhSMxH.Z6SrR6GEifZiRtRW8O	user	0	0	0	t	f	2026-01-04 10:46:47.294309	2026-01-04 10:46:47.294309	\N
17	wangzihe	wangzihe@mathtasks.com	$2b$12$Zn3EVOh7IclIDkCxCISgGeetHcklcxUFCQvz24PH3lL0KjHyOfkIy	user	0	0	0	t	f	2026-01-04 10:46:47.294309	2026-01-04 10:46:47.29431	\N
18	zhangyilian	zhangyilian@mathtasks.com	$2b$12$tJ9VAe2gIqbJVpy./zYSz..NZyls/fOU0Aa1LAayxSwC/Qk7VzfBy	user	0	0	0	t	f	2026-01-04 10:46:47.29431	2026-01-04 10:46:47.29431	\N
19	chenbosheng	chenbosheng@mathtasks.com	$2b$12$amA3mI8TgCZCWM5qH.FffuT/ovLBf6ERNxPle4fH367neePHIrtPO	user	0	0	0	t	f	2026-01-04 10:46:47.29431	2026-01-04 10:46:47.294311	\N
20	zuoyuxiang	zuoyuxiang@mathtasks.com	$2b$12$VSN9JrL.ZCGBzA8cq920X.Q7c8LjSRvxygBE/cuBumpBUD1aWpFDC	user	0	0	0	t	f	2026-01-04 10:46:47.294311	2026-01-04 10:46:47.294311	\N
21	zhouyu	zhouyu@mathtasks.com	$2b$12$3TzJSV3tUGzy699jfy.B9u.gIEBvHOc1FLr71twWlZN5SaLS/cm/S	user	0	0	0	t	f	2026-01-04 10:46:47.294311	2026-01-04 10:46:47.294312	\N
4	chenjinyi	chenjinyi@mathtasks.com	$2b$12$SZc4q2HYo9gikBH4AW7CT.ilsgaAPUIO7.r8U421WAbNj7MI6Gfj2	user	10	0	1	t	f	2026-01-04 10:46:47.294302	2026-01-04 10:48:56.261887	2026-01-04 10:47:44.51062
\.


--
-- Data for Name: validated_problem_exports; Type: TABLE DATA; Schema: public; Owner: mathtasks
--

COPY public.validated_problem_exports (id, user_id, task_id, content, answer, explanation, difficulty_validation, originality_check, rigor_check, review_count, avg_innovation_score, avg_rigor_score, admin_review_status, admin_reviewer_id, admin_review_note, admin_reviewed_at, created_at) FROM stdin;
1	1	1	Calculate the number of disjoint time intervals within the interval [0,1] where the combined sound intensity, modeled by \\( f(x) = \\log_{10} (\\sin(\\pi x) \\cdot \\sin(2\\pi x) \\cdot \\sin(3\\pi x) \\cdots \\sin(8\\pi x)) \\), exceeds a threshold of 0 decibels. The intensity is only measurable when the argument of the logarithm is positive.	12	The problem requires determining the number of disjoint open intervals where the function is defined, which corresponds to the intervals where the argument of the logarithm is positive (since the logarithm is undefined for non-positive values). The function’s argument is a product of sine functions: \\( \\sin(\\pi x) \\cdot \\sin(2\\pi x) \\cdot \\sin(3\\pi x) \\cdots \\sin(8\\pi x) \\). For the logarithm to be defined, this product must be strictly greater than zero.  \nStep 1: Identify the zeros of each sine factor. For a general term \\( \\sin(k\\pi x) \\) where \\( k = 1, 2, \\ldots, 8 \\), the zeros occur when \\( k\\pi x = n\\pi \\) for some integer \\( n \\), which simplifies to \\( x = \\frac{n}{k} \\). We consider \\( x \\) in the interval \\( [0, 1] \\) (since the function is periodic with period 1, and the behavior in \\( [0,1] \\) determines the behavior in other intervals due to periodicity).  \nStep 2: List the zeros for each \\( k \\):  \n- For \\( k = 1 \\): \\( \\sin(\\pi x) = 0 \\) when \\( x = 0, 1 \\).  \n- For \\( k = 2 \\): \\( \\sin(2\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{2}, 1 \\).  \n- For \\( k = 3 \\): \\( \\sin(3\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{3}, \\frac{2}{3}, 1 \\).  \n- For \\( k = 4 \\): \\( \\sin(4\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{4}, \\frac{2}{4}, \\frac{3}{4}, 1 \\).  \n- For \\( k = 5 \\): \\( \\sin(5\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{5}, \\frac{2}{5}, \\frac{3}{5}, \\frac{4}{5}, 1 \\).  \n- For \\( k = 6 \\): \\( \\sin(6\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{6}, \\frac{2}{6}, \\frac{3}{6}, \\frac{4}{6}, \\frac{5}{6}, 1 \\).  \n- For \\( k = 7 \\): \\( \\sin(7\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{7}, \\frac{2}{7}, \\frac{3}{7}, \\frac{4}{7}, \\frac{5}{7}, \\frac{6}{7}, 1 \\).  \n- For \\( k = 8 \\): \\( \\sin(8\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{8}, \\frac{2}{8}, \\frac{3}{8}, \\frac{4}{8}, \\frac{5}{8}, \\frac{6}{8}, \\frac{7}{8}, 1 \\).  \nStep 3: Count the total number of distinct zeros. To avoid double-counting, we list all unique values of \\( x \\) from the above. The distinct zeros are: 0, \\( \\frac{1}{8} \\), \\( \\frac{1}{7} \\), \\( \\frac{1}{6} \\), \\( \\frac{1}{5} \\), \\( \\frac{1}{4} \\), \\( \\frac{2}{7} \\), \\( \\frac{1}{3} \\), \\( \\frac{3}{8} \\), \\( \\frac{2}{5} \\), \\( \\frac{3}{7} \\), \\( \\frac{1}{2} \\), \\( \\frac{4}{7} \\), \\( \\frac{3}{5} \\), \\( \\frac{5}{8} \\), \\( \\frac{2}{3} \\), \\( \\frac{5}{7} \\), \\( \\frac{3}{4} \\), \\( \\frac{4}{5} \\), \\( \\frac{5}{6} \\), \\( \\frac{6}{7} \\), \\( \\frac{7}{8} \\), 1. Counting these, we find there are 23 distinct zeros.  \nStep 4: Determine the number of intervals between consecutive zeros. Since there are 23 zeros, the number of open intervals between them is \\( 23 - 1 = 22 \\).  \nStep 5: Analyze the sign of the product \\( \\sin(\\pi x) \\cdot \\sin(2\\pi x) \\cdots \\sin(8\\pi x) \\) in each interval. The sign of the product changes at each zero, except when a zero is of even multiplicity (i.e., a zero is shared by an even number of sine factors), in which case the sign does not change. We first check the sign in the first interval \\( (0, \\frac{1}{8}) \\). For \\( x \\) in this interval, all \\( \\sin(k\\pi x) \\) terms are positive (since \\( k\\pi x \\) is in \\( (0, \\frac{k\\pi}{8}) \\), and for \\( k \\leq 8 \\), \\( \\frac{k\\pi}{8} \\leq \\pi \\), so sine is positive in \\( (0, \\pi) \\)). Thus, the product is positive in \\( (0, \\frac{1}{8}) \\).  \nStep 6: Determine the sign in subsequent intervals. Since the sign changes at each simple zero (multiplicity 1) and remains the same at zeros of even multiplicity, we track the sign alternation. The next interval \\( (\\frac{1}{8}, \\frac{1}{7}) \\) has one zero at \\( \\frac{1}{8} \\) (from \\( \\sin(8\\pi x) \\)), so the sign flips to negative. Continuing this pattern, we count the number of negative intervals.  \nStep 7: Use symmetry to simplify. The function \\( f(x) = \\sin(\\pi x) \\cdot \\sin(2\\pi x) \\cdots \\sin(8\\pi x) \\) is symmetric about \\( x = \\frac{1}{2} \\) (i.e., \\( f(1 - x) = f(x) \\) for all \\( x \\)). This symmetry implies that the number of negative intervals in \\( [0, \\frac{1}{2}] \\) is equal to the number of negative intervals in \\( [\\frac{1}{2}, 1] \\). From the sign analysis, we find there are 5 negative intervals in \\( [0, \\frac{1}{2}] \\), so there are also 5 negative intervals in \\( [\\frac{1}{2}, 1] \\), giving a total of \\( 5 + 5 = 10 \\) negative intervals.  \nStep 8: Calculate the number of positive intervals. The total number of intervals is 22, and the number of negative intervals is 10. Therefore, the number of positive intervals (where the function is defined) is \\( 22 - 10 = 12 \\).	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.777880"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.777890"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.777892"}	0	\N	\N	approved	\N	\N	\N	2026-01-04 10:46:56.777904
8	1	1	Determine the slope of the other common external tangent line that passes through the origin, given that in a Cartesian coordinate system, two circles have a common point at (9,6), both are tangent to the x-axis, and the product of their radius is 68.	\\frac{12\\sqrt{221}}{49}	Step 1: Since the line connecting the centers of the two circles passes through the origin, we can denote the centers of the two circles as \\((a, ka)\\) and \\((b, kb)\\), where \\(k\\) represents the slope of the line through the origin.  \nStep 2: For the first circle with center \\((a, ka)\\), the distance from its center to the point \\((9, 6)\\) must equal its radius. This gives the equation \\((a - 9)^2 + (ka - 6)^2 = (ka)^2\\). Expanding the left-hand side, we obtain \\(a^2 - 18a + 81 + k^2a^2 - 12ka + 36 = k^2a^2\\). Simplifying by canceling \\(k^2a^2\\) from both sides and combining like terms, we get \\(a^2 - 18a + 117 - 12ka = 0\\). Rearranging terms to form a quadratic equation in \\(a\\), we have \\(a^2 - 6(2k + 3)a + 117 = 0\\).  \nStep 3: Similarly, for the second circle with center \\((b, kb)\\), applying the same distance condition to the point \\((9, 6)\\) yields \\((b - 9)^2 + (kb - 6)^2 = (kb)^2\\). Expanding and simplifying this equation as in Step 2 results in \\(b^2 - 6(2k + 3)b + 117 = 0\\).  \nStep 4: Since \\(a \\neq b\\), both \\(a\\) and \\(b\\) are distinct roots of the quadratic equation \\(x^2 - 6(2k + 3)x + 117 = 0\\). By Vieta's formulas, the product of the roots \\(ab\\) is equal to the constant term of the quadratic, so \\(ab = 117\\).  \nStep 5: The product of the \\(y\\)-coordinates of the centers is \\(ka \\cdot kb = k^2ab\\). We are given that this product equals 68, so \\(k^2ab = 68\\). Substituting \\(ab = 117\\) from Step 4, we obtain \\(k^2 \\cdot 117 = 68\\). Solving for \\(k^2\\), we find \\(k^2 = \\frac{68}{117}\\), and thus \\(k = \\sqrt{\\frac{68}{117}} = \\frac{2\\sqrt{17}}{3\\sqrt{13}}\\) (after rationalizing the denominator).  \nStep 6: The slope of the other external common tangent is given by the formula \\(\\frac{2k}{1 - k^2}\\). Substituting \\(k^2 = \\frac{68}{117}\\), we first calculate the denominator: \\(1 - \\frac{68}{117} = \\frac{117 - 68}{117} = \\frac{49}{117}\\). Then the slope becomes \\(\\frac{2k}{\\frac{49}{117}} = 2k \\cdot \\frac{117}{49}\\). Substituting \\(k = \\frac{2\\sqrt{17}}{3\\sqrt{13}}\\), we get \\(2 \\cdot \\frac{2\\sqrt{17}}{3\\sqrt{13}} \\cdot \\frac{117}{49} = \\frac{4\\sqrt{17} \\cdot 117}{3\\sqrt{13} \\cdot 49}\\). Simplifying \\(\\frac{117}{3} = 39\\), this reduces to \\(\\frac{4\\sqrt{17} \\cdot 39}{\\sqrt{13} \\cdot 49} = \\frac{156\\sqrt{17}}{49\\sqrt{13}}\\). Rationalizing the denominator by multiplying the numerator and denominator by \\(\\sqrt{13}\\), we obtain \\(\\frac{156\\sqrt{17} \\cdot \\sqrt{13}}{49 \\cdot 13} = \\frac{156\\sqrt{221}}{637}\\). Since \\(\\frac{156}{13} = 12\\), this simplifies to \\(\\frac{12\\sqrt{221}}{49}\\).	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.844436"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.844445"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.844447"}	0	5	5	approved	\N	\N	\N	2026-01-04 10:46:56.844454
3	1	1	Calculate the number of disjoint time intervals within the one-second recording period [0,1] where the combined audio signal strength, modeled by f(x) = log_{10}(sin(\\pi x) \\cdot sin(2\\pi x) \\cdot sin(3\\pi x) \\cdots sin(8\\pi x)), exceeds the minimum audible threshold of 0 decibels. The signal amplitude is only detectable when the argument of the logarithm is positive.	12	The problem requires determining the number of disjoint open intervals where the function is defined, which corresponds to the intervals where the argument of the logarithm is positive (since the logarithm is undefined for non-positive values). The function’s argument is a product of sine functions: \\( \\sin(\\pi x) \\cdot \\sin(2\\pi x) \\cdot \\sin(3\\pi x) \\cdots \\sin(8\\pi x) \\). For the logarithm to be defined, this product must be strictly greater than zero.  \nStep 1: Identify the zeros of each sine factor. For a general term \\( \\sin(k\\pi x) \\) where \\( k = 1, 2, \\ldots, 8 \\), the zeros occur when \\( k\\pi x = n\\pi \\) for some integer \\( n \\), which simplifies to \\( x = \\frac{n}{k} \\). We consider \\( x \\) in the interval \\( [0, 1] \\) (since the function is periodic with period 1, and the behavior in \\( [0,1] \\) determines the behavior in other intervals due to periodicity).  \nStep 2: List the zeros for each \\( k \\):  \n- For \\( k = 1 \\): \\( \\sin(\\pi x) = 0 \\) when \\( x = 0, 1 \\).  \n- For \\( k = 2 \\): \\( \\sin(2\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{2}, 1 \\).  \n- For \\( k = 3 \\): \\( \\sin(3\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{3}, \\frac{2}{3}, 1 \\).  \n- For \\( k = 4 \\): \\( \\sin(4\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{4}, \\frac{2}{4}, \\frac{3}{4}, 1 \\).  \n- For \\( k = 5 \\): \\( \\sin(5\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{5}, \\frac{2}{5}, \\frac{3}{5}, \\frac{4}{5}, 1 \\).  \n- For \\( k = 6 \\): \\( \\sin(6\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{6}, \\frac{2}{6}, \\frac{3}{6}, \\frac{4}{6}, \\frac{5}{6}, 1 \\).  \n- For \\( k = 7 \\): \\( \\sin(7\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{7}, \\frac{2}{7}, \\frac{3}{7}, \\frac{4}{7}, \\frac{5}{7}, \\frac{6}{7}, 1 \\).  \n- For \\( k = 8 \\): \\( \\sin(8\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{8}, \\frac{2}{8}, \\frac{3}{8}, \\frac{4}{8}, \\frac{5}{8}, \\frac{6}{8}, \\frac{7}{8}, 1 \\).  \nStep 3: Count the total number of distinct zeros. To avoid double-counting, we list all unique values of \\( x \\) from the above. The distinct zeros are: 0, \\( \\frac{1}{8} \\), \\( \\frac{1}{7} \\), \\( \\frac{1}{6} \\), \\( \\frac{1}{5} \\), \\( \\frac{1}{4} \\), \\( \\frac{2}{7} \\), \\( \\frac{1}{3} \\), \\( \\frac{3}{8} \\), \\( \\frac{2}{5} \\), \\( \\frac{3}{7} \\), \\( \\frac{1}{2} \\), \\( \\frac{4}{7} \\), \\( \\frac{3}{5} \\), \\( \\frac{5}{8} \\), \\( \\frac{2}{3} \\), \\( \\frac{5}{7} \\), \\( \\frac{3}{4} \\), \\( \\frac{4}{5} \\), \\( \\frac{5}{6} \\), \\( \\frac{6}{7} \\), \\( \\frac{7}{8} \\), 1. Counting these, we find there are 23 distinct zeros.  \nStep 4: Determine the number of intervals between consecutive zeros. Since there are 23 zeros, the number of open intervals between them is \\( 23 - 1 = 22 \\).  \nStep 5: Analyze the sign of the product \\( \\sin(\\pi x) \\cdot \\sin(2\\pi x) \\cdots \\sin(8\\pi x) \\) in each interval. The sign of the product changes at each zero, except when a zero is of even multiplicity (i.e., a zero is shared by an even number of sine factors), in which case the sign does not change. We first check the sign in the first interval \\( (0, \\frac{1}{8}) \\). For \\( x \\) in this interval, all \\( \\sin(k\\pi x) \\) terms are positive (since \\( k\\pi x \\) is in \\( (0, \\frac{k\\pi}{8}) \\), and for \\( k \\leq 8 \\), \\( \\frac{k\\pi}{8} \\leq \\pi \\), so sine is positive in \\( (0, \\pi) \\)). Thus, the product is positive in \\( (0, \\frac{1}{8}) \\).  \nStep 6: Determine the sign in subsequent intervals. Since the sign changes at each simple zero (multiplicity 1) and remains the same at zeros of even multiplicity, we track the sign alternation. The next interval \\( (\\frac{1}{8}, \\frac{1}{7}) \\) has one zero at \\( \\frac{1}{8} \\) (from \\( \\sin(8\\pi x) \\)), so the sign flips to negative. Continuing this pattern, we count the number of negative intervals.  \nStep 7: Use symmetry to simplify. The function \\( f(x) = \\sin(\\pi x) \\cdot \\sin(2\\pi x) \\cdots \\sin(8\\pi x) \\) is symmetric about \\( x = \\frac{1}{2} \\) (i.e., \\( f(1 - x) = f(x) \\) for all \\( x \\)). This symmetry implies that the number of negative intervals in \\( [0, \\frac{1}{2}] \\) is equal to the number of negative intervals in \\( [\\frac{1}{2}, 1] \\). From the sign analysis, we find there are 5 negative intervals in \\( [0, \\frac{1}{2}] \\), so there are also 5 negative intervals in \\( [\\frac{1}{2}, 1] \\), giving a total of \\( 5 + 5 = 10 \\) negative intervals.  \nStep 8: Calculate the number of positive intervals. The total number of intervals is 22, and the number of negative intervals is 10. Therefore, the number of positive intervals (where the function is defined) is \\( 22 - 10 = 12 \\).	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.802294"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.802302"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.802304"}	0	\N	\N	approved	\N	\N	\N	2026-01-04 10:46:56.802312
2	1	1	An audio engineer is analyzing a complex sound wave composed of multiple frequency components. The combined intensity of the sound is modeled by the function \\( f(x) = \\log_{10} \\left( \\sin(\\pi x) \\cdot \\sin(2\\pi x) \\cdot \\sin(3\\pi x) \\cdots \\sin(8\\pi x) \\right) \\), where \\( x \\) represents time in seconds within the interval [0,1]. The engineer defines a sound as "audible" when its intensity exceeds 0 decibels, which corresponds to the condition that the argument of the logarithm is greater than 1 (since \\( \\log_{10}(1) = 0 \\)). Determine the number of disjoint open time intervals within [0,1] where the sound is audible.	12	The problem requires determining the number of disjoint open intervals where the function is defined, which corresponds to the intervals where the argument of the logarithm is positive (since the logarithm is undefined for non-positive values). The function’s argument is a product of sine functions: \\( \\sin(\\pi x) \\cdot \\sin(2\\pi x) \\cdot \\sin(3\\pi x) \\cdots \\sin(8\\pi x) \\). For the logarithm to be defined, this product must be strictly greater than zero.  \nStep 1: Identify the zeros of each sine factor. For a general term \\( \\sin(k\\pi x) \\) where \\( k = 1, 2, \\ldots, 8 \\), the zeros occur when \\( k\\pi x = n\\pi \\) for some integer \\( n \\), which simplifies to \\( x = \\frac{n}{k} \\). We consider \\( x \\) in the interval \\( [0, 1] \\) (since the function is periodic with period 1, and the behavior in \\( [0,1] \\) determines the behavior in other intervals due to periodicity).  \nStep 2: List the zeros for each \\( k \\):  \n- For \\( k = 1 \\): \\( \\sin(\\pi x) = 0 \\) when \\( x = 0, 1 \\).  \n- For \\( k = 2 \\): \\( \\sin(2\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{2}, 1 \\).  \n- For \\( k = 3 \\): \\( \\sin(3\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{3}, \\frac{2}{3}, 1 \\).  \n- For \\( k = 4 \\): \\( \\sin(4\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{4}, \\frac{2}{4}, \\frac{3}{4}, 1 \\).  \n- For \\( k = 5 \\): \\( \\sin(5\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{5}, \\frac{2}{5}, \\frac{3}{5}, \\frac{4}{5}, 1 \\).  \n- For \\( k = 6 \\): \\( \\sin(6\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{6}, \\frac{2}{6}, \\frac{3}{6}, \\frac{4}{6}, \\frac{5}{6}, 1 \\).  \n- For \\( k = 7 \\): \\( \\sin(7\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{7}, \\frac{2}{7}, \\frac{3}{7}, \\frac{4}{7}, \\frac{5}{7}, \\frac{6}{7}, 1 \\).  \n- For \\( k = 8 \\): \\( \\sin(8\\pi x) = 0 \\) when \\( x = 0, \\frac{1}{8}, \\frac{2}{8}, \\frac{3}{8}, \\frac{4}{8}, \\frac{5}{8}, \\frac{6}{8}, \\frac{7}{8}, 1 \\).  \nStep 3: Count the total number of distinct zeros. To avoid double-counting, we list all unique values of \\( x \\) from the above. The distinct zeros are: 0, \\( \\frac{1}{8} \\), \\( \\frac{1}{7} \\), \\( \\frac{1}{6} \\), \\( \\frac{1}{5} \\), \\( \\frac{1}{4} \\), \\( \\frac{2}{7} \\), \\( \\frac{1}{3} \\), \\( \\frac{3}{8} \\), \\( \\frac{2}{5} \\), \\( \\frac{3}{7} \\), \\( \\frac{1}{2} \\), \\( \\frac{4}{7} \\), \\( \\frac{3}{5} \\), \\( \\frac{5}{8} \\), \\( \\frac{2}{3} \\), \\( \\frac{5}{7} \\), \\( \\frac{3}{4} \\), \\( \\frac{4}{5} \\), \\( \\frac{5}{6} \\), \\( \\frac{6}{7} \\), \\( \\frac{7}{8} \\), 1. Counting these, we find there are 23 distinct zeros.  \nStep 4: Determine the number of intervals between consecutive zeros. Since there are 23 zeros, the number of open intervals between them is \\( 23 - 1 = 22 \\).  \nStep 5: Analyze the sign of the product \\( \\sin(\\pi x) \\cdot \\sin(2\\pi x) \\cdots \\sin(8\\pi x) \\) in each interval. The sign of the product changes at each zero, except when a zero is of even multiplicity (i.e., a zero is shared by an even number of sine factors), in which case the sign does not change. We first check the sign in the first interval \\( (0, \\frac{1}{8}) \\). For \\( x \\) in this interval, all \\( \\sin(k\\pi x) \\) terms are positive (since \\( k\\pi x \\) is in \\( (0, \\frac{k\\pi}{8}) \\), and for \\( k \\leq 8 \\), \\( \\frac{k\\pi}{8} \\leq \\pi \\), so sine is positive in \\( (0, \\pi) \\)). Thus, the product is positive in \\( (0, \\frac{1}{8}) \\).  \nStep 6: Determine the sign in subsequent intervals. Since the sign changes at each simple zero (multiplicity 1) and remains the same at zeros of even multiplicity, we track the sign alternation. The next interval \\( (\\frac{1}{8}, \\frac{1}{7}) \\) has one zero at \\( \\frac{1}{8} \\) (from \\( \\sin(8\\pi x) \\)), so the sign flips to negative. Continuing this pattern, we count the number of negative intervals.  \nStep 7: Use symmetry to simplify. The function \\( f(x) = \\sin(\\pi x) \\cdot \\sin(2\\pi x) \\cdots \\sin(8\\pi x) \\) is symmetric about \\( x = \\frac{1}{2} \\) (i.e., \\( f(1 - x) = f(x) \\) for all \\( x \\)). This symmetry implies that the number of negative intervals in \\( [0, \\frac{1}{2}] \\) is equal to the number of negative intervals in \\( [\\frac{1}{2}, 1] \\). From the sign analysis, we find there are 5 negative intervals in \\( [0, \\frac{1}{2}] \\), so there are also 5 negative intervals in \\( [\\frac{1}{2}, 1] \\), giving a total of \\( 5 + 5 = 10 \\) negative intervals.  \nStep 8: Calculate the number of positive intervals. The total number of intervals is 22, and the number of negative intervals is 10. Therefore, the number of positive intervals (where the function is defined) is \\( 22 - 10 = 12 \\).	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.794260"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.794270"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.794273"}	0	\N	\N	approved	\N	\N	\N	2026-01-04 10:46:56.794282
4	1	1	A tetrahedral container ABCD is filled with liquid. Points P, Q, R, S are located on edges AB, BD, CD, CA respectively such that \\( \\frac{AP}{PB} = \\frac{AS}{SC} = 1 \\) and \\( \\frac{BQ}{QD} = \\frac{CR}{RD} = \\frac{1}{2} \\). A plane passing through points P, Q, R, S divides the container into two parts. Find the ratio of the volumes of the two parts (smaller to larger).	\\frac{13}{23}	Step 1: As shown in the figure, by the given conditions, line segments \\( PS \\) and \\( QR \\) are both parallel to line segment \\( BC \\). Consequently, points \\( P, Q, R, S \\) are coplanar, and the plane containing them is parallel to \\( BC \\). Now, construct line segment \\( SX \\) parallel to \\( BP \\) and line segment \\( SY \\) parallel to \\( PQ \\), intersecting \\( BC \\) at point \\( X \\) and \\( QR \\) at point \\( Y \\), respectively. In this manner, the solid \\( PBQRCS \\) is partitioned into a triangular prism \\( BPQ-XSY \\) and a quadrilateral pyramid \\( S-XYRC \\).  \nStep 2: Let the volume of tetrahedron \\( A-BCD \\) be denoted as \\( V_{A-BCD} = 1 \\). To calculate the volume \\( V_1 \\) of the triangular prism \\( BPQ-XSY \\), we use the formula for the volume of a prism: \\( V_1 = 3 \\times \\frac{PS}{BC} \\times \\frac{S_{\\Delta BPQ}}{S_{\\Delta BAD}} \\). Substituting the given ratios \\( \\frac{PS}{BC} = \\frac{1}{2} \\) and \\( \\frac{S_{\\Delta BPQ}}{S_{\\Delta BAD}} = \\frac{1}{3} \\) into the formula, we obtain:  \n\\[ V_1 = 3 \\times \\frac{1}{2} \\times \\frac{1}{3} = \\frac{1}{4} \\]  \nStep 3: Next, we calculate the volume \\( V_2 \\) of the quadrilateral pyramid \\( S-XYRC \\). The formula for the volume of a pyramid is \\( V_2 = \\frac{SC}{AC} \\times \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} \\). To find \\( \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} \\), we first identify point \\( Z \\) as the intersection of line segment \\( XY \\) and line segment \\( CD \\). Calculating the length of \\( RZ \\):  \n\\[ RZ = CZ - CR = \\frac{1}{2}CD - \\frac{1}{3}CD = \\frac{1}{6}CD \\]  \nSince triangles \\( YZR \\) and \\( XZC \\) are similar (due to the parallelism of \\( SY \\) to \\( PQ \\) and the coplanarity of points), the ratio of their areas is the square of the ratio of their corresponding sides:  \n\\[ \\frac{S_{\\Delta YZR}}{S_{\\Delta XZC}} = \\left( \\frac{RZ}{CZ} \\right)^2 = \\left( \\frac{\\frac{1}{6}CD}{\\frac{1}{2}CD} \\right)^2 = \\left( \\frac{1}{3} \\right)^2 = \\frac{1}{9} \\]  \nThus, the area of triangle \\( XRC \\) is:  \n\\[ S_{\\Delta XRC} = S_{\\Delta XZC} - S_{\\Delta YZR} = S_{\\Delta XZC} - \\frac{1}{9}S_{\\Delta XZC} = \\frac{8}{9}S_{\\Delta XZC} \\]  \nNext, we determine the ratio \\( \\frac{S_{\\Delta XZC}}{S_{\\Delta BCD}} \\). Since \\( X \\) lies on \\( BC \\) and \\( Z \\) lies on \\( CD \\), and the plane containing \\( P, Q, R, S \\) is parallel to \\( BC \\), line segment \\( XZ \\) is parallel to \\( BC \\). Therefore, triangle \\( XZC \\) is similar to triangle \\( BCD \\) with a similarity ratio of \\( \\frac{CZ}{CD} = \\frac{1}{2} \\). The ratio of their areas is the square of the similarity ratio:  \n\\[ \\frac{S_{\\Delta XZC}}{S_{\\Delta BCD}} = \\left( \\frac{1}{2} \\right)^2 = \\frac{1}{4} \\]  \nSubstituting this into the expression for \\( S_{\\Delta XRC} \\), we get:  \n\\[ \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} = \\frac{8}{9} \\times \\frac{1}{4} = \\frac{2}{9} \\]  \nNow, substituting \\( \\frac{SC}{AC} = \\frac{1}{2} \\) and \\( \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} = \\frac{2}{9} \\) into the formula for \\( V_2 \\):  \n\\[ V_2 = \\frac{1}{2} \\times \\frac{2}{9} = \\frac{1}{9} \\]  \nStep 4: The total volume of the solid \\( PBQRCS \\) is the sum of \\( V_1 \\) and \\( V_2 \\):  \n\\[ V_1 + V_2 = \\frac{1}{4} + \\frac{1}{9} = \\frac{9}{36} + \\frac{4}{36} = \\frac{13}{36} \\]  \nThe ratio of the smaller volume to the larger volume is:  \n\\[ \\frac{\\text{Smaller Volume}}{\\text{Larger Volume}} = \\frac{13}{23} \\]	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.810450"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.810460"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.810461"}	0	\N	\N	approved	\N	\N	\N	2026-01-04 10:46:56.810469
5	1	1	A tetrahedral chemical reactor ABCD is filled with a liquid reactant. Points P, Q, R, S are located on edges AB, BD, CD, CA respectively such that \\( \\frac{AP}{PB} = \\frac{AS}{SC} = 1 \\) and \\( \\frac{BQ}{QD} = \\frac{CR}{RD} = \\frac{1}{2} \\). A partition plane passing through points P, Q, R, S divides the reactor into two parts. Determine the ratio of the volumes of the two parts (smaller to larger).	\\frac{13}{23}	Step 1: As shown in the figure, by the given conditions, line segments \\( PS \\) and \\( QR \\) are both parallel to line segment \\( BC \\). Consequently, points \\( P, Q, R, S \\) are coplanar, and the plane containing them is parallel to \\( BC \\). Now, construct line segment \\( SX \\) parallel to \\( BP \\) and line segment \\( SY \\) parallel to \\( PQ \\), intersecting \\( BC \\) at point \\( X \\) and \\( QR \\) at point \\( Y \\), respectively. In this manner, the solid \\( PBQRCS \\) is partitioned into a triangular prism \\( BPQ-XSY \\) and a quadrilateral pyramid \\( S-XYRC \\).  \nStep 2: Let the volume of tetrahedron \\( A-BCD \\) be denoted as \\( V_{A-BCD} = 1 \\). To calculate the volume \\( V_1 \\) of the triangular prism \\( BPQ-XSY \\), we use the formula for the volume of a prism: \\( V_1 = 3 \\times \\frac{PS}{BC} \\times \\frac{S_{\\Delta BPQ}}{S_{\\Delta BAD}} \\). Substituting the given ratios \\( \\frac{PS}{BC} = \\frac{1}{2} \\) and \\( \\frac{S_{\\Delta BPQ}}{S_{\\Delta BAD}} = \\frac{1}{3} \\) into the formula, we obtain:  \n\\[ V_1 = 3 \\times \\frac{1}{2} \\times \\frac{1}{3} = \\frac{1}{4} \\]  \nStep 3: Next, we calculate the volume \\( V_2 \\) of the quadrilateral pyramid \\( S-XYRC \\). The formula for the volume of a pyramid is \\( V_2 = \\frac{SC}{AC} \\times \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} \\). To find \\( \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} \\), we first identify point \\( Z \\) as the intersection of line segment \\( XY \\) and line segment \\( CD \\). Calculating the length of \\( RZ \\):  \n\\[ RZ = CZ - CR = \\frac{1}{2}CD - \\frac{1}{3}CD = \\frac{1}{6}CD \\]  \nSince triangles \\( YZR \\) and \\( XZC \\) are similar (due to the parallelism of \\( SY \\) to \\( PQ \\) and the coplanarity of points), the ratio of their areas is the square of the ratio of their corresponding sides:  \n\\[ \\frac{S_{\\Delta YZR}}{S_{\\Delta XZC}} = \\left( \\frac{RZ}{CZ} \\right)^2 = \\left( \\frac{\\frac{1}{6}CD}{\\frac{1}{2}CD} \\right)^2 = \\left( \\frac{1}{3} \\right)^2 = \\frac{1}{9} \\]  \nThus, the area of triangle \\( XRC \\) is:  \n\\[ S_{\\Delta XRC} = S_{\\Delta XZC} - S_{\\Delta YZR} = S_{\\Delta XZC} - \\frac{1}{9}S_{\\Delta XZC} = \\frac{8}{9}S_{\\Delta XZC} \\]  \nNext, we determine the ratio \\( \\frac{S_{\\Delta XZC}}{S_{\\Delta BCD}} \\). Since \\( X \\) lies on \\( BC \\) and \\( Z \\) lies on \\( CD \\), and the plane containing \\( P, Q, R, S \\) is parallel to \\( BC \\), line segment \\( XZ \\) is parallel to \\( BC \\). Therefore, triangle \\( XZC \\) is similar to triangle \\( BCD \\) with a similarity ratio of \\( \\frac{CZ}{CD} = \\frac{1}{2} \\). The ratio of their areas is the square of the similarity ratio:  \n\\[ \\frac{S_{\\Delta XZC}}{S_{\\Delta BCD}} = \\left( \\frac{1}{2} \\right)^2 = \\frac{1}{4} \\]  \nSubstituting this into the expression for \\( S_{\\Delta XRC} \\), we get:  \n\\[ \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} = \\frac{8}{9} \\times \\frac{1}{4} = \\frac{2}{9} \\]  \nNow, substituting \\( \\frac{SC}{AC} = \\frac{1}{2} \\) and \\( \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} = \\frac{2}{9} \\) into the formula for \\( V_2 \\):  \n\\[ V_2 = \\frac{1}{2} \\times \\frac{2}{9} = \\frac{1}{9} \\]  \nStep 4: The total volume of the solid \\( PBQRCS \\) is the sum of \\( V_1 \\) and \\( V_2 \\):  \n\\[ V_1 + V_2 = \\frac{1}{4} + \\frac{1}{9} = \\frac{9}{36} + \\frac{4}{36} = \\frac{13}{36} \\]  \nThe ratio of the smaller volume to the larger volume is:  \n\\[ \\frac{\\text{Smaller Volume}}{\\text{Larger Volume}} = \\frac{13}{23} \\]	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.818659"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.818670"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.818672"}	0	\N	\N	approved	\N	\N	\N	2026-01-04 10:46:56.81868
6	1	1	An industrial facility has a tetrahedral storage tank ABCD filled with chemical solution. Points P, Q, R, S are located on edges AB, BD, CD, CA respectively such that \\( \\frac{AP}{PB} = \\frac{AS}{SC} = 1 \\) and \\( \\frac{BQ}{QD} = \\frac{CR}{RD} = \\frac{1}{2} \\). A plane passing through points P, Q, R, S divides the tank into two parts. Find the ratio of the volumes of the two parts (smaller to larger).	\\frac{13}{23}	Step 1: As shown in the figure, by the given conditions, line segments \\( PS \\) and \\( QR \\) are both parallel to line segment \\( BC \\). Consequently, points \\( P, Q, R, S \\) are coplanar, and the plane containing them is parallel to \\( BC \\). Now, construct line segment \\( SX \\) parallel to \\( BP \\) and line segment \\( SY \\) parallel to \\( PQ \\), intersecting \\( BC \\) at point \\( X \\) and \\( QR \\) at point \\( Y \\), respectively. In this manner, the solid \\( PBQRCS \\) is partitioned into a triangular prism \\( BPQ-XSY \\) and a quadrilateral pyramid \\( S-XYRC \\).  \nStep 2: Let the volume of tetrahedron \\( A-BCD \\) be denoted as \\( V_{A-BCD} = 1 \\). To calculate the volume \\( V_1 \\) of the triangular prism \\( BPQ-XSY \\), we use the formula for the volume of a prism: \\( V_1 = 3 \\times \\frac{PS}{BC} \\times \\frac{S_{\\Delta BPQ}}{S_{\\Delta BAD}} \\). Substituting the given ratios \\( \\frac{PS}{BC} = \\frac{1}{2} \\) and \\( \\frac{S_{\\Delta BPQ}}{S_{\\Delta BAD}} = \\frac{1}{3} \\) into the formula, we obtain:  \n\\[ V_1 = 3 \\times \\frac{1}{2} \\times \\frac{1}{3} = \\frac{1}{4} \\]  \nStep 3: Next, we calculate the volume \\( V_2 \\) of the quadrilateral pyramid \\( S-XYRC \\). The formula for the volume of a pyramid is \\( V_2 = \\frac{SC}{AC} \\times \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} \\). To find \\( \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} \\), we first identify point \\( Z \\) as the intersection of line segment \\( XY \\) and line segment \\( CD \\). Calculating the length of \\( RZ \\):  \n\\[ RZ = CZ - CR = \\frac{1}{2}CD - \\frac{1}{3}CD = \\frac{1}{6}CD \\]  \nSince triangles \\( YZR \\) and \\( XZC \\) are similar (due to the parallelism of \\( SY \\) to \\( PQ \\) and the coplanarity of points), the ratio of their areas is the square of the ratio of their corresponding sides:  \n\\[ \\frac{S_{\\Delta YZR}}{S_{\\Delta XZC}} = \\left( \\frac{RZ}{CZ} \\right)^2 = \\left( \\frac{\\frac{1}{6}CD}{\\frac{1}{2}CD} \\right)^2 = \\left( \\frac{1}{3} \\right)^2 = \\frac{1}{9} \\]  \nThus, the area of triangle \\( XRC \\) is:  \n\\[ S_{\\Delta XRC} = S_{\\Delta XZC} - S_{\\Delta YZR} = S_{\\Delta XZC} - \\frac{1}{9}S_{\\Delta XZC} = \\frac{8}{9}S_{\\Delta XZC} \\]  \nNext, we determine the ratio \\( \\frac{S_{\\Delta XZC}}{S_{\\Delta BCD}} \\). Since \\( X \\) lies on \\( BC \\) and \\( Z \\) lies on \\( CD \\), and the plane containing \\( P, Q, R, S \\) is parallel to \\( BC \\), line segment \\( XZ \\) is parallel to \\( BC \\). Therefore, triangle \\( XZC \\) is similar to triangle \\( BCD \\) with a similarity ratio of \\( \\frac{CZ}{CD} = \\frac{1}{2} \\). The ratio of their areas is the square of the similarity ratio:  \n\\[ \\frac{S_{\\Delta XZC}}{S_{\\Delta BCD}} = \\left( \\frac{1}{2} \\right)^2 = \\frac{1}{4} \\]  \nSubstituting this into the expression for \\( S_{\\Delta XRC} \\), we get:  \n\\[ \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} = \\frac{8}{9} \\times \\frac{1}{4} = \\frac{2}{9} \\]  \nNow, substituting \\( \\frac{SC}{AC} = \\frac{1}{2} \\) and \\( \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} = \\frac{2}{9} \\) into the formula for \\( V_2 \\):  \n\\[ V_2 = \\frac{1}{2} \\times \\frac{2}{9} = \\frac{1}{9} \\]  \nStep 4: The total volume of the solid \\( PBQRCS \\) is the sum of \\( V_1 \\) and \\( V_2 \\):  \n\\[ V_1 + V_2 = \\frac{1}{4} + \\frac{1}{9} = \\frac{9}{36} + \\frac{4}{36} = \\frac{13}{36} \\]  \nThe ratio of the smaller volume to the larger volume is:  \n\\[ \\frac{\\text{Smaller Volume}}{\\text{Larger Volume}} = \\frac{13}{23} \\]	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.828398"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.828408"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.828410"}	0	\N	\N	approved	\N	\N	\N	2026-01-04 10:46:56.828418
7	1	1	A pyramid-shaped grain silo ABCD is constructed from concrete. Points P, Q, R, S are located on edges AB, BD, CD, CA respectively such that the ratios AP:PB and AS:SC both equal 1:1, while the ratios BQ:QD and CR:RD both equal 1:2. A partition wall passing through points P, Q, R, S divides the silo into two compartments. Determine the ratio of the volumes of the two compartments (smaller to larger).	\\frac{13}{23}	Step 1: As shown in the figure, by the given conditions, line segments \\( PS \\) and \\( QR \\) are both parallel to line segment \\( BC \\). Consequently, points \\( P, Q, R, S \\) are coplanar, and the plane containing them is parallel to \\( BC \\). Now, construct line segment \\( SX \\) parallel to \\( BP \\) and line segment \\( SY \\) parallel to \\( PQ \\), intersecting \\( BC \\) at point \\( X \\) and \\( QR \\) at point \\( Y \\), respectively. In this manner, the solid \\( PBQRCS \\) is partitioned into a triangular prism \\( BPQ-XSY \\) and a quadrilateral pyramid \\( S-XYRC \\).  \nStep 2: Let the volume of tetrahedron \\( A-BCD \\) be denoted as \\( V_{A-BCD} = 1 \\). To calculate the volume \\( V_1 \\) of the triangular prism \\( BPQ-XSY \\), we use the formula for the volume of a prism: \\( V_1 = 3 \\times \\frac{PS}{BC} \\times \\frac{S_{\\Delta BPQ}}{S_{\\Delta BAD}} \\). Substituting the given ratios \\( \\frac{PS}{BC} = \\frac{1}{2} \\) and \\( \\frac{S_{\\Delta BPQ}}{S_{\\Delta BAD}} = \\frac{1}{3} \\) into the formula, we obtain:  \n\\[ V_1 = 3 \\times \\frac{1}{2} \\times \\frac{1}{3} = \\frac{1}{4} \\]  \nStep 3: Next, we calculate the volume \\( V_2 \\) of the quadrilateral pyramid \\( S-XYRC \\). The formula for the volume of a pyramid is \\( V_2 = \\frac{SC}{AC} \\times \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} \\). To find \\( \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} \\), we first identify point \\( Z \\) as the intersection of line segment \\( XY \\) and line segment \\( CD \\). Calculating the length of \\( RZ \\):  \n\\[ RZ = CZ - CR = \\frac{1}{2}CD - \\frac{1}{3}CD = \\frac{1}{6}CD \\]  \nSince triangles \\( YZR \\) and \\( XZC \\) are similar (due to the parallelism of \\( SY \\) to \\( PQ \\) and the coplanarity of points), the ratio of their areas is the square of the ratio of their corresponding sides:  \n\\[ \\frac{S_{\\Delta YZR}}{S_{\\Delta XZC}} = \\left( \\frac{RZ}{CZ} \\right)^2 = \\left( \\frac{\\frac{1}{6}CD}{\\frac{1}{2}CD} \\right)^2 = \\left( \\frac{1}{3} \\right)^2 = \\frac{1}{9} \\]  \nThus, the area of triangle \\( XRC \\) is:  \n\\[ S_{\\Delta XRC} = S_{\\Delta XZC} - S_{\\Delta YZR} = S_{\\Delta XZC} - \\frac{1}{9}S_{\\Delta XZC} = \\frac{8}{9}S_{\\Delta XZC} \\]  \nNext, we determine the ratio \\( \\frac{S_{\\Delta XZC}}{S_{\\Delta BCD}} \\). Since \\( X \\) lies on \\( BC \\) and \\( Z \\) lies on \\( CD \\), and the plane containing \\( P, Q, R, S \\) is parallel to \\( BC \\), line segment \\( XZ \\) is parallel to \\( BC \\). Therefore, triangle \\( XZC \\) is similar to triangle \\( BCD \\) with a similarity ratio of \\( \\frac{CZ}{CD} = \\frac{1}{2} \\). The ratio of their areas is the square of the similarity ratio:  \n\\[ \\frac{S_{\\Delta XZC}}{S_{\\Delta BCD}} = \\left( \\frac{1}{2} \\right)^2 = \\frac{1}{4} \\]  \nSubstituting this into the expression for \\( S_{\\Delta XRC} \\), we get:  \n\\[ \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} = \\frac{8}{9} \\times \\frac{1}{4} = \\frac{2}{9} \\]  \nNow, substituting \\( \\frac{SC}{AC} = \\frac{1}{2} \\) and \\( \\frac{S_{\\Delta XRC}}{S_{\\Delta BCD}} = \\frac{2}{9} \\) into the formula for \\( V_2 \\):  \n\\[ V_2 = \\frac{1}{2} \\times \\frac{2}{9} = \\frac{1}{9} \\]  \nStep 4: The total volume of the solid \\( PBQRCS \\) is the sum of \\( V_1 \\) and \\( V_2 \\):  \n\\[ V_1 + V_2 = \\frac{1}{4} + \\frac{1}{9} = \\frac{9}{36} + \\frac{4}{36} = \\frac{13}{36} \\]  \nThe ratio of the smaller volume to the larger volume is:  \n\\[ \\frac{\\text{Smaller Volume}}{\\text{Larger Volume}} = \\frac{13}{23} \\]	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.836874"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.836884"}	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.836885"}	0	\N	\N	approved	\N	\N	\N	2026-01-04 10:46:56.836892
\.


--
-- Data for Name: validation_records; Type: TABLE DATA; Schema: public; Owner: mathtasks
--

COPY public.validation_records (id, validated_problem_id, validation_type, ai_model, attempts, correct_count, is_passed, result_data, created_at) FROM stdin;
1	1	difficulty	imported	\N	\N	t	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.777880"}	2026-01-04 10:46:56.782913
2	1	originality	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.777890"}	2026-01-04 10:46:56.782974
3	1	rigor	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.777892"}	2026-01-04 10:46:56.782991
4	2	difficulty	imported	\N	\N	t	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.794260"}	2026-01-04 10:46:56.795713
5	2	originality	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.794270"}	2026-01-04 10:46:56.795741
6	2	rigor	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.794273"}	2026-01-04 10:46:56.795754
7	3	difficulty	imported	\N	\N	t	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.802294"}	2026-01-04 10:46:56.803549
8	3	originality	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.802302"}	2026-01-04 10:46:56.80358
9	3	rigor	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.802304"}	2026-01-04 10:46:56.803595
10	4	difficulty	imported	\N	\N	t	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.810450"}	2026-01-04 10:46:56.811868
11	4	originality	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.810460"}	2026-01-04 10:46:56.811897
12	4	rigor	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.810461"}	2026-01-04 10:46:56.811907
13	5	difficulty	imported	\N	\N	t	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.818659"}	2026-01-04 10:46:56.820122
14	5	originality	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.818670"}	2026-01-04 10:46:56.820157
15	5	rigor	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.818672"}	2026-01-04 10:46:56.82017
16	6	difficulty	imported	\N	\N	t	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.828398"}	2026-01-04 10:46:56.829873
17	6	originality	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.828408"}	2026-01-04 10:46:56.829912
18	6	rigor	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.828410"}	2026-01-04 10:46:56.829922
19	7	difficulty	imported	\N	\N	t	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.836874"}	2026-01-04 10:46:56.838226
20	7	originality	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.836884"}	2026-01-04 10:46:56.838261
21	7	rigor	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.836885"}	2026-01-04 10:46:56.838272
22	8	difficulty	imported	\N	\N	t	{"success": true, "difficulty_level": "\\u4e2d\\u5b66", "confidence": 0.85, "timestamp": "2026-01-04T10:46:56.844436"}	2026-01-04 10:46:56.845571
23	8	originality	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.844445"}	2026-01-04 10:46:56.845603
24	8	rigor	imported	\N	\N	t	{"success": true, "passed": true, "score": 8.5, "reasoning": "\\u9898\\u76ee\\u8d28\\u91cf\\u826f\\u597d\\uff0c\\u7b26\\u5408\\u6807\\u51c6", "timestamp": "2026-01-04T10:46:56.844447"}	2026-01-04 10:46:56.845613
\.


--
-- Name: material_library_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mathtasks
--

SELECT pg_catalog.setval('public.material_library_id_seq', 12, true);


--
-- Name: problems_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mathtasks
--

SELECT pg_catalog.setval('public.problems_id_seq', 1, false);


--
-- Name: reviews_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mathtasks
--

SELECT pg_catalog.setval('public.reviews_id_seq', 40, true);


--
-- Name: tasks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mathtasks
--

SELECT pg_catalog.setval('public.tasks_id_seq', 6, true);


--
-- Name: transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mathtasks
--

SELECT pg_catalog.setval('public.transactions_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mathtasks
--

SELECT pg_catalog.setval('public.users_id_seq', 21, true);


--
-- Name: validated_problem_exports_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mathtasks
--

SELECT pg_catalog.setval('public.validated_problem_exports_id_seq', 8, true);


--
-- Name: validation_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mathtasks
--

SELECT pg_catalog.setval('public.validation_records_id_seq', 24, true);


--
-- Name: material_library material_library_pkey; Type: CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.material_library
    ADD CONSTRAINT material_library_pkey PRIMARY KEY (id);


--
-- Name: problems problems_pkey; Type: CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.problems
    ADD CONSTRAINT problems_pkey PRIMARY KEY (id);


--
-- Name: reviews reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_pkey PRIMARY KEY (id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: validated_problem_exports validated_problem_exports_pkey; Type: CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.validated_problem_exports
    ADD CONSTRAINT validated_problem_exports_pkey PRIMARY KEY (id);


--
-- Name: validation_records validation_records_pkey; Type: CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.validation_records
    ADD CONSTRAINT validation_records_pkey PRIMARY KEY (id);


--
-- Name: idx_created_at; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX idx_created_at ON public.transactions USING btree (created_at);


--
-- Name: idx_creator_status; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX idx_creator_status ON public.problems USING btree (creator_id, status);


--
-- Name: idx_expires_at; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX idx_expires_at ON public.tasks USING btree (expires_at);


--
-- Name: idx_problem_reviewer; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX idx_problem_reviewer ON public.reviews USING btree (problem_id, reviewer_id);


--
-- Name: idx_problem_status; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX idx_problem_status ON public.tasks USING btree (problem_id, status);


--
-- Name: idx_reviewer_status; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX idx_reviewer_status ON public.reviews USING btree (reviewer_id, status);


--
-- Name: idx_user_status; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX idx_user_status ON public.tasks USING btree (user_id, status);


--
-- Name: idx_user_type_status; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX idx_user_type_status ON public.transactions USING btree (user_id, transaction_type, status);


--
-- Name: idx_validated_problem_type; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX idx_validated_problem_type ON public.validation_records USING btree (validated_problem_id, validation_type);


--
-- Name: idx_validation_status; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX idx_validation_status ON public.problems USING btree (validation_status, status);


--
-- Name: ix_material_library_category; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_material_library_category ON public.material_library USING btree (category);


--
-- Name: ix_material_library_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_material_library_id ON public.material_library USING btree (id);


--
-- Name: ix_problems_category; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_problems_category ON public.problems USING btree (category);


--
-- Name: ix_problems_created_at; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_problems_created_at ON public.problems USING btree (created_at);


--
-- Name: ix_problems_creator_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_problems_creator_id ON public.problems USING btree (creator_id);


--
-- Name: ix_problems_human_review_status; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_problems_human_review_status ON public.problems USING btree (human_review_status);


--
-- Name: ix_problems_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_problems_id ON public.problems USING btree (id);


--
-- Name: ix_problems_mongo_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE UNIQUE INDEX ix_problems_mongo_id ON public.problems USING btree (mongo_id);


--
-- Name: ix_problems_parent_problem_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_problems_parent_problem_id ON public.problems USING btree (parent_problem_id);


--
-- Name: ix_problems_status; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_problems_status ON public.problems USING btree (status);


--
-- Name: ix_problems_validation_status; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_problems_validation_status ON public.problems USING btree (validation_status);


--
-- Name: ix_reviews_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_reviews_id ON public.reviews USING btree (id);


--
-- Name: ix_reviews_problem_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_reviews_problem_id ON public.reviews USING btree (problem_id);


--
-- Name: ix_reviews_reviewer_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_reviews_reviewer_id ON public.reviews USING btree (reviewer_id);


--
-- Name: ix_reviews_status; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_reviews_status ON public.reviews USING btree (status);


--
-- Name: ix_reviews_task_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_reviews_task_id ON public.reviews USING btree (task_id);


--
-- Name: ix_reviews_validated_problem_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_reviews_validated_problem_id ON public.reviews USING btree (validated_problem_id);


--
-- Name: ix_tasks_batch_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_tasks_batch_id ON public.tasks USING btree (batch_id);


--
-- Name: ix_tasks_expires_at; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_tasks_expires_at ON public.tasks USING btree (expires_at);


--
-- Name: ix_tasks_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_tasks_id ON public.tasks USING btree (id);


--
-- Name: ix_tasks_problem_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_tasks_problem_id ON public.tasks USING btree (problem_id);


--
-- Name: ix_tasks_status; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_tasks_status ON public.tasks USING btree (status);


--
-- Name: ix_tasks_user_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_tasks_user_id ON public.tasks USING btree (user_id);


--
-- Name: ix_tasks_validated_problem_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_tasks_validated_problem_id ON public.tasks USING btree (validated_problem_id);


--
-- Name: ix_transactions_created_at; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_transactions_created_at ON public.transactions USING btree (created_at);


--
-- Name: ix_transactions_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_transactions_id ON public.transactions USING btree (id);


--
-- Name: ix_transactions_status; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_transactions_status ON public.transactions USING btree (status);


--
-- Name: ix_transactions_transaction_type; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_transactions_transaction_type ON public.transactions USING btree (transaction_type);


--
-- Name: ix_transactions_user_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_transactions_user_id ON public.transactions USING btree (user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: ix_validated_problem_exports_admin_review_status; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_validated_problem_exports_admin_review_status ON public.validated_problem_exports USING btree (admin_review_status);


--
-- Name: ix_validated_problem_exports_created_at; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_validated_problem_exports_created_at ON public.validated_problem_exports USING btree (created_at);


--
-- Name: ix_validated_problem_exports_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_validated_problem_exports_id ON public.validated_problem_exports USING btree (id);


--
-- Name: ix_validated_problem_exports_task_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_validated_problem_exports_task_id ON public.validated_problem_exports USING btree (task_id);


--
-- Name: ix_validated_problem_exports_user_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_validated_problem_exports_user_id ON public.validated_problem_exports USING btree (user_id);


--
-- Name: ix_validation_records_created_at; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_validation_records_created_at ON public.validation_records USING btree (created_at);


--
-- Name: ix_validation_records_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_validation_records_id ON public.validation_records USING btree (id);


--
-- Name: ix_validation_records_validated_problem_id; Type: INDEX; Schema: public; Owner: mathtasks
--

CREATE INDEX ix_validation_records_validated_problem_id ON public.validation_records USING btree (validated_problem_id);


--
-- Name: problems problems_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.problems
    ADD CONSTRAINT problems_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.users(id);


--
-- Name: problems problems_parent_problem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.problems
    ADD CONSTRAINT problems_parent_problem_id_fkey FOREIGN KEY (parent_problem_id) REFERENCES public.problems(id);


--
-- Name: reviews reviews_problem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_problem_id_fkey FOREIGN KEY (problem_id) REFERENCES public.problems(id);


--
-- Name: reviews reviews_reviewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_reviewer_id_fkey FOREIGN KEY (reviewer_id) REFERENCES public.users(id);


--
-- Name: reviews reviews_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id);


--
-- Name: reviews reviews_validated_problem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_validated_problem_id_fkey FOREIGN KEY (validated_problem_id) REFERENCES public.validated_problem_exports(id) ON DELETE CASCADE;


--
-- Name: tasks tasks_problem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_problem_id_fkey FOREIGN KEY (problem_id) REFERENCES public.problems(id);


--
-- Name: tasks tasks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: tasks tasks_validated_problem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_validated_problem_id_fkey FOREIGN KEY (validated_problem_id) REFERENCES public.validated_problem_exports(id) ON DELETE CASCADE;


--
-- Name: transactions transactions_related_problem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_related_problem_id_fkey FOREIGN KEY (related_problem_id) REFERENCES public.problems(id);


--
-- Name: transactions transactions_related_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_related_task_id_fkey FOREIGN KEY (related_task_id) REFERENCES public.tasks(id);


--
-- Name: transactions transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: validated_problem_exports validated_problem_exports_admin_reviewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.validated_problem_exports
    ADD CONSTRAINT validated_problem_exports_admin_reviewer_id_fkey FOREIGN KEY (admin_reviewer_id) REFERENCES public.users(id);


--
-- Name: validated_problem_exports validated_problem_exports_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.validated_problem_exports
    ADD CONSTRAINT validated_problem_exports_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id);


--
-- Name: validated_problem_exports validated_problem_exports_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.validated_problem_exports
    ADD CONSTRAINT validated_problem_exports_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: validation_records validation_records_validated_problem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mathtasks
--

ALTER TABLE ONLY public.validation_records
    ADD CONSTRAINT validation_records_validated_problem_id_fkey FOREIGN KEY (validated_problem_id) REFERENCES public.validated_problem_exports(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict wEBYH7dksULysN1lP1lHPguUXV84rvV9SPcBTPp0pTVRxPmH0cSQZfcECw4Do8I

