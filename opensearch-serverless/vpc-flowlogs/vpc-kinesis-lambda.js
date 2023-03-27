console.log('Loading function');
  
exports.handler = async (event, context) => {
    let success = 0; // Number of valid entries found
    let failure = 0; // Number of invalid entries found
 
    /* Process the list of records and transform them */
    const output = event.records.map((record) => {
        // Kinesis data is base64 encoded so decode here
        console.log(record.recordId);
        
        const payload = (Buffer.from(record.data, 'base64')).toString('ascii');
        console.log(payload);
        var payload_dict = JSON.parse(payload);
        
        const split_payload = payload_dict["message"].split(" ");
        const result = {
          timestamp: new Date().toISOString(),
          version: parseInt(split_payload[0]),
          account_id: split_payload[1],
          interface_id: split_payload[2],
          srcaddr: split_payload[3],
          dstaddr: split_payload[4],
          srcport: parseInt(split_payload[5]),
          dstport: parseInt(split_payload[6]),
          protocol: split_payload[7],
          packets: parseInt(split_payload[8]),
          bytes: parseInt(split_payload[9]),
          start: new Date(parseInt(split_payload[10]) * 1000).toISOString(),
          end: new Date(parseInt(split_payload[11]) * 1000).toISOString(),
          action: split_payload[12],
          log_status: split_payload[13]
        };
        success++;
        return {
            recordId: record.recordId,
            result: 'Ok',
            data: (Buffer.from(JSON.stringify(result))).toString('base64'),
        };
    });
    console.log(`Processing completed.  Successful records ${success}, Failed records ${failure}.`);    
    return { records: output };
};
 

