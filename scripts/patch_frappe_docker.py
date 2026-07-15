#!/usr/bin/env python3
import sys
from pathlib import Path


def replace_once(content: str, old: str, new: str, label: str) -> str:
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one {label} insertion point, found {count}")
    return content.replace(old, new, 1)


path = Path(sys.argv[1])
content = path.read_text(encoding="utf-8")

content = replace_once(
    content,
    "ENV PATH=${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}\n\nRUN useradd",
    "ENV PATH=${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}\n\n"
    "COPY image-manifest.json /opt/frappe/image-manifest.json\n\nRUN useradd",
    "image manifest",
)

content = replace_once(
    content,
    'ARG CACHE_BUST=""\n\nRUN --mount',
    'ARG CACHE_BUST=""\n'
    "ARG FRAPPE_COMMIT\n"
    "ARG ERPNEXT_COMMIT\n"
    "ARG HRMS_COMMIT\n"
    "ARG PAYMENTS_COMMIT\n\n"
    "RUN --mount",
    "commit arguments",
)

content = replace_once(
    content,
    "  cd /home/frappe/frappe-bench && \\\n"
    '  echo "{}" > sites/common_site_config.json',
    "  cd /home/frappe/frappe-bench && \\\n"
    '  test -n "${FRAPPE_COMMIT}" && \\\n'
    '  test -n "${ERPNEXT_COMMIT}" && \\\n'
    '  test -n "${HRMS_COMMIT}" && \\\n'
    '  test -n "${PAYMENTS_COMMIT}" && \\\n'
    '  git -C apps/payments fetch --depth 1 origin "${PAYMENTS_COMMIT}" && \\\n'
    '  git -C apps/payments checkout --detach "${PAYMENTS_COMMIT}" && \\\n'
    "  bench setup requirements --python && \\\n"
    "  bench build --production && \\\n"
    '  test "$(git -C apps/frappe rev-parse HEAD)" = "${FRAPPE_COMMIT}" && \\\n'
    '  test "$(git -C apps/erpnext rev-parse HEAD)" = "${ERPNEXT_COMMIT}" && \\\n'
    '  test "$(git -C apps/hrms rev-parse HEAD)" = "${HRMS_COMMIT}" && \\\n'
    '  test "$(git -C apps/payments rev-parse HEAD)" = "${PAYMENTS_COMMIT}" && \\\n'
    '  echo "{}" > sites/common_site_config.json',
    "commit verification",
)

path.write_text(content, encoding="utf-8")
print(f"patched builder: {path}")
