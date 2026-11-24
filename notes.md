SLO for the assignment:
  slo : 
    min_rate : 19.6,
    min_fidelity : 0.7769,
    max_p95_latency_ms : 573.25
  


For link 0-1 :

attempt rate = 4.0641
probability of success = 0.00707

Therefore, success rate = 4.0641 * 0.00707 = 0.028733187 pairs per ms.
That is, 
    28.733 pairs per sec.


For link 1-2 : 

attempt_rate = 4.5625
probability of success = 0.0281

success rate = 4.5625 * 0.0281 = 0.12820625 pairs per ms.
That is,
    128.206 pairs per sec.


link 1-2 is 5 times faster than link 01.


Policy Making : 
    The baseline policy is First in First out for ebits, with  swaps as soon as possible both links have a pair ready. This means, the ebit which arrived last should wait till both has a pair. This caused decay in the coherence of ebits. Also, as there is no ebit expiration. Therefore, we are creating a policy which implements LAST IN FIRST OUT for ebits.


    Purification done? 
        No, because, the bottleneck link, which is link 0-1 has a pair generation rate of 28.7 pairs per second. If we do purification, it will be cut in half to 14.4 pairs per sec. This would immediately breach the SLO of 19.6 pairs per sec.




