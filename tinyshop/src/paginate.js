function paginate(list, page = 1, size = 10) {
  const start = (page - 1) * size;
  return {
    items: list.slice(start, start + size),
    page,
    size,
    total: list.length,
    pages: Math.ceil(list.length / size),
  };
}

module.exports = { paginate };
