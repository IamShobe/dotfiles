local setup, illuminate = pcall(require, "illuminate")
if not setup then
  return
end

illuminate.configure()
