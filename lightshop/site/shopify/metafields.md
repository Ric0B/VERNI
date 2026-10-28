# Product metafield definitions

Create these once in Shopify admin > Settings > Custom data > Products (namespace `custom`) before importing `products.csv`, so the theme's spec table and badges fill in.

| Name | Key | Type |
|---|---|---|
| Layers | custom.layers | number_integer |
| Print hours | custom.print_hours | number_integer |
| Height cm | custom.height_cm | number_decimal |
| Diameter cm | custom.diameter_cm | number_decimal |
| Material | custom.material | single_line_text_field |
| Light | custom.light | single_line_text_field |
| Power | custom.power | single_line_text_field |
| Cable | custom.cable | single_line_text_field |
| Edition | custom.edition | single_line_text_field |
| Tagline | custom.tagline | single_line_text_field |
