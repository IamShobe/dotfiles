-- import comment plugin safely
local setup, bufferline = pcall(require, "bufferline")
if not setup then
  return
end

-- enable comment
bufferline.setup()
