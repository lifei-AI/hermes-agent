"""
Hermes 补丁验证脚本 — 升级后运行，确认所有定制改动正确生效
用法: cd ~/.hermes/hermes-agent && python3 verify_patches.py
"""
import sys
sys.path.insert(0, '.')

errors = []

# 1. 模拟服务器启动（无 ContextVar）
from run_agent import AIAgent

# 2. 模拟用户请求到来（设 ContextVar）
from hermes_constants import set_hermes_home_override
TEST_HOME = '/tmp/verify_patch_home'
set_hermes_home_override(TEST_HOME)

# 3. 检查动态路径函数
import tools.skills_tool as st
r = str(st._skills_dir())
if r != f'{TEST_HOME}/skills':
    errors.append(f'skills_tool._skills_dir() = {r}, expected {TEST_HOME}/skills')

import tools.skill_manager_tool as smt
r = str(smt._skills_dir())
if r != f'{TEST_HOME}/skills':
    errors.append(f'skill_manager_tool._skills_dir() = {r}, expected {TEST_HOME}/skills')

import cron.jobs as cj
r = str(cj._jobs_file())
if r != f'{TEST_HOME}/cron/jobs.json':
    errors.append(f'cron.jobs._jobs_file() = {r}, expected {TEST_HOME}/cron/jobs.json')

r = str(cj._output_dir())
if r != f'{TEST_HOME}/cron/output':
    errors.append(f'cron.jobs._output_dir() = {r}, expected {TEST_HOME}/cron/output')

# 4. 确认旧常量已移除
try:
    from cron.jobs import OUTPUT_DIR
    errors.append('cron.jobs.OUTPUT_DIR still exists (should be _output_dir)')
except ImportError:
    pass

try:
    from tools.skills_tool import SKILLS_DIR
    errors.append('tools.skills_tool.SKILLS_DIR still exists (should be _skills_dir)')
except ImportError:
    pass

# 5. 检查 hermes_state 动态路径
from hermes_state import _default_db_path
r = str(_default_db_path())
if r != f'{TEST_HOME}/state.db':
    errors.append(f'hermes_state._default_db_path() = {r}, expected {TEST_HOME}/state.db')

# 6. 检查 file_tools ContextVar cwd
from agent.runtime_cwd import set_session_cwd
set_session_cwd(f'{TEST_HOME}/files')
from tools.file_tools import _configured_terminal_cwd
r = _configured_terminal_cwd()
if r != f'{TEST_HOME}/files':
    errors.append(f'file_tools._configured_terminal_cwd() = {r}, expected {TEST_HOME}/files')

# 7. 检查 cron.scheduler 中 _output_dir 可导入
try:
    from cron.jobs import _output_dir as _od
    r = str(_od())
    if r != f'{TEST_HOME}/cron/output':
        errors.append(f'cron.jobs._output_dir() via scheduler = {r}, expected {TEST_HOME}/cron/output')
except ImportError as e:
    errors.append(f'cron.jobs._output_dir not importable: {e}')

# 8. 多用户隔离测试
for uid in ['user_A', 'user_B']:
    set_hermes_home_override(f'/tmp/{uid}')
    r = str(st._skills_dir())
    if r != f'/tmp/{uid}/skills':
        errors.append(f'Isolation failure: skills_tool for {uid} = {r}')

# 输出结果
if errors:
    print('❌ 验证失败:')
    for e in errors:
        print(f'  - {e}')
    sys.exit(1)
else:
    print('✅ 所有补丁验证通过')
    sys.exit(0)
