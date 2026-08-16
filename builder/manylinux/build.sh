#!/bin/bash
set -e -x

PYBINS=("/opt/python/cp311-cp311/bin" "/opt/python/cp312-cp312/bin" "/opt/python/cp313-cp313/bin" "/opt/python/cp314-cp314/bin")
RUST_CHANNEL=stable

ls -la /opt/python/

function install_rust {
    curl https://sh.rustup.rs -sSf | sh -s -- -y
    source "$HOME/.cargo/env"
}

function clean_project {
    # Remove compiled files that might cause conflicts
    pushd /io/
    rm -rf .cache build *.egg-info rust/target
    find ./ -name "__pycache__" -type d -print0 |xargs -0 rm -rf
    find ./ -name "*.pyc" -type f -print0 |xargs -0 rm -rf
    find ./ -name "*.so" -type f -print0 |xargs -0 rm -rf
    popd
}

clean_project
install_rust $RUST_CHANNEL
rm -rf /io/builder/manylinux/wheelhouse/* || echo "No old wheels to delete"
mkdir -p /io/builder/manylinux/wheelhouse
mkdir -p /io/dist

for PYBIN in ${PYBINS[@]}; do
    ${PYBIN}/python -m pip wheel /io -w /io/builder/manylinux/wheelhouse/ --no-deps
done

for whl in /io/builder/manylinux/wheelhouse/aardwolf*.whl; do
    auditwheel repair $whl -w /io/dist/
done
clean_project
