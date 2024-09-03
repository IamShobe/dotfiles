local cmp_status, neoclip = pcall(require, "neoclip")
if not cmp_status then
  return
end

neoclip.setup()
