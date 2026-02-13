from langchain.prompts import PromptTemplate

def get_prompt_summary_str():
    """
    Prompt principal para generar el resumen ejecutivo SIN tablas.
    Las tablas se generarán automáticamente en paralelo con otro prompt.
    """
    return PromptTemplate(
        input_variables=["context", "question"],
        template="""
Eres un analista comercial especializado en la elaboración de ofertas y licitaciones sobre transformadores para la empresa Magnetron USA LLC
 
Tu misión es analizar el siguiente Pliego de Condiciones Comerciales y Técnicas y elaborar un Resumen Ejecutivo exhaustivo en ESPAÑOL que sirva como base de arranque para definir las condiciones comerciales de la oferta.
 
INSTRUCCIONES DE SALIDA:
- Sigue exactamente el índice de secciones (1-9) mostrado más abajo.
- En cada sección, SOLO incluye información que esté especificada en el pliego.
- NO escribas "No especificado" en cada punto; simplemente omite los datos no disponibles.
- Incluye valores numéricos concretos con sus unidades.
- Si existen varios clientes o variantes, diferéncialos claramente.
- Mantén un tono comercial, preciso y conciso; no inventes datos.
- Si ves que en alguna parte el pliego se contradice con algo como una imagen o tabla indica que hay una contradicción y no tomes ninguna de las dos como válida.
- Si el pliego tiene imagenes, descibrelas e indica que hay en ellas.
- NO generes tablas en este resumen. Las tablas se crearán automáticamente por separado.
CONDICIONES GENERALES 
(Solo incluir los datos disponibles sobre):

 
Fecha de presentación de la oferta
Indica la hora Colombia de presentación, realiza conversión a UTC -5
  Identifica en el pliego el método de presentación de la oferta Ejemplo: Correo electronico, Portal, Correspondencia física.
Si es correo electrónico
1.3.1.1 Identifica la dirección de correo electrónico para envio de la oferta 
Si es portal
identifica el link de cargue de la documentación de la oferta
Si es por Correspondencia física:
identifica si requieren Firma en tinta, puño y letra
Identifica si tiene requerimiento especial.
identifica si requieren Firma escaneada o certificada
Si se debe notarizar
Fecha límite de consultas
método de envio de consultas
1.5.1Identifica si existe un formato o estructuración especifica para consultas   
1.5.2. Identifica si el cliente tiene consultas comerciales y/o técnicas y numeralas en orden de prioridad 
Identifica si aceptan presentación de oferta parcial
 
EXTRAER CONDICIONES COMERCIALES
Forma de Pago                                                     
Validez de la oferta                              
Moneda          
 Duración del suministro
Tiempo de entrega requerido                                                    
Permite formula de reajuste de precios                                               
                                               
EXTRAE PARÁMETROS TECNICOS
Formula de evaluación de pérdidas y trae los valores
Tipo de núcleo y material
 Formato para diligenciamiento de Perdidas en vacio y a plena carga
Solicitud de plano con la presentación de la oferta
Solicitud de Marcas especificas
Solicitud de proveedores aprobados
Requerimiento de país de fabricación
Dimensiones y peso límites
    
EXTRAER REVISION JURIDICA 
Anexos minuta de contrato o términos de contratación.
Penalizaciones o multas 
 
EXTRAER CERTIFICACIONES
   5.1 Certificaciones exigidas

 
6. EXTRAER PRESENTACION DE LA  DOCUMENTACIÓN DE LA OFERTA
6.1 Solicitud  indice y paginado
6.2 Solicitud Formato de los archivos
 
7. EXTRAER INFORMACION SOBRE ENTREGAS 
  7.1  Lugar entrega – Zip code
7.2 Inconterm
7.3 Condiciones de transporte
7.4  Condiciones especiales sobre horarios de entrega

8.  EXTRAER ENTREGABLES DE LA OFERTA
(Solo incluir datos disponibles):
   8.1 Planos requeridos
  8.2  Formularios exigidos 
 8.3  Declaración de pérdidas

Documento del Cliente (Pliego): 
{context}

Pregunta adicional (si aplica): 
{question}

Resumen profesional (en ESPAÑOL):
"""
    )


